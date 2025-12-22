from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string

from django.contrib.auth.models import User

from .models import Conversation, Message, Document
from .forms import SignUpForm, DocumentUploadForm

from .ai_model import generate_ai_reply, generate_ai_title
from .analyzer import extract_text_from_file
from .chroma_manager import add_document, query_document


# -------------------------
# AUTH VIEWS
# -------------------------

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("conversations_list")

        return render(request, "chat/login.html", {"error": "Invalid credentials"})

    return render(request, "chat/login.html")


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            return render(request, "chat/signup.html", {"error": "Passwords do not match"})

        if User.objects.filter(username=username).exists():
            return render(request, "chat/signup.html", {"error": "Username already exists"})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        login(request, user)
        return redirect("conversations_list")

    return render(request, "chat/signup.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# -------------------------
# CHAT VIEWS
# -------------------------

@login_required
def conversations_list(request):
    conversations = Conversation.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(request, "chat/conversations.html", {
        "all_conversations": conversations,
        "conversation": None,
    })


@login_required
def conversation_detail(request, conv_id=None):
    all_conversations = Conversation.objects.filter(
        user=request.user
    ).order_by("-created_at")

    # Create new conversation
    if conv_id is None:
        conv = Conversation.objects.create(
            user=request.user,
            title="New Chat"
        )
        return redirect("conversation_detail", conv_id=conv.id)

    conv = get_object_or_404(
        Conversation,
        id=conv_id,
        user=request.user
    )

    # -------------------------
    # HANDLE USER MESSAGE
    # -------------------------
    if request.method == "POST" and "text" in request.POST:
        user_message = request.POST.get("text", "").strip()

        if user_message:
            # Save user message
            Message.objects.create(
                conversation=conv,
                user=request.user,
                text=user_message,
                is_bot=False
            )

            # Auto-generate title
            if conv.title == "New Chat":
                conv.title = generate_ai_title(user_message)
                conv.save()

            # 🔍 Query Chroma for document context
            relevant_chunks = query_document(conv.id, user_message)

            if not relevant_chunks:
                ai_response = "No relevant information found in the uploaded document."
            else:
                context = "\n\n".join(relevant_chunks)
                prompt = f"""
You are an assistant answering questions strictly from the document context below.

DOCUMENT CONTEXT:
{context}

QUESTION:
{user_message}

Answer based only on the document.
"""
                ai_response = generate_ai_reply(prompt)

            # Save AI message
            Message.objects.create(
                conversation=conv,
                user=request.user,
                text=ai_response,
                is_bot=True
            )

        return redirect("conversation_detail", conv_id=conv.id)

    # -------------------------
    # HANDLE DOCUMENT UPLOAD
    # -------------------------
    if request.method == "POST" and "file" in request.FILES:
        upload_form = DocumentUploadForm(request.POST, request.FILES)

        if upload_form.is_valid():
            doc = upload_form.save(commit=False)
            doc.user = request.user
            doc.conversation = conv
            doc.save()

            extracted_text = extract_text_from_file(doc.file.path)
            if extracted_text.strip():
                # 🧠 Store document in Chroma under this conversation
                add_document(conv.id, extracted_text)

        return redirect("conversation_detail", conv_id=conv.id)

    upload_form = DocumentUploadForm()
    messages = conv.messages.order_by("timestamp")
    documents = conv.documents.order_by("-uploaded_at")

    return render(request, "chat/conversation.html", {
        "conversation": conv,
        "messages": messages,
        "upload_form": upload_form,
        "documents": documents,
        "all_conversations": all_conversations,
    })


# -------------------------
# AJAX PARTIAL
# -------------------------

@login_required
def messages_partial(request, conv_id):
    conv = get_object_or_404(
        Conversation,
        id=conv_id,
        user=request.user
    )

    messages = conv.messages.order_by("timestamp")
    html = render_to_string(
        "chat/messages_list.html",
        {"messages": messages},
        request=request
    )

    return JsonResponse({"html": html})
