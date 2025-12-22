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
from .chroma_manager import add_document_to_chroma, query_document


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
    from .chroma_manager import query_document, add_document_to_chroma
    from .analyzer import extract_text_from_file

    all_conversations = Conversation.objects.filter(
        user=request.user
    ).order_by("-created_at")

    # Create new conversation if none exists
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

    # -----------------------------
    # USER MESSAGE (CHAT)
    # -----------------------------
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

            # Generate title only once
            if conv.title == "New Chat":
                try:
                    conv.title = generate_ai_title(user_message)
                    conv.save()
                except Exception:
                    pass

            # ---- RAG SEARCH ----
            relevant_chunks = []
            try:
                relevant_chunks = query_document(conv.id, user_message)
            except Exception:
                relevant_chunks = []

            # Build prompt
            if relevant_chunks:
                context = "\n\n".join(relevant_chunks)
                prompt = f"""
You are an assistant answering strictly from the document below.

DOCUMENT:
{context}

QUESTION:
{user_message}

Answer only using the document.
"""
            else:
                prompt = user_message

            # Generate AI response
            try:
                ai_response = generate_ai_reply(prompt)
            except Exception:
                ai_response = "AI is temporarily unavailable."

            # Save bot message
            Message.objects.create(
                conversation=conv,
                user=request.user,
                text=ai_response,
                is_bot=True
            )

        return redirect("conversation_detail", conv_id=conv.id)

    # -----------------------------
    # DOCUMENT UPLOAD
    # -----------------------------
    if request.method == "POST" and "file" in request.FILES:
        upload_form = DocumentUploadForm(request.POST, request.FILES)

        if upload_form.is_valid():
            doc = upload_form.save(commit=False)
            doc.user = request.user
            doc.conversation = conv
            doc.save()

            extracted_text = extract_text_from_file(doc.file.path)
            print("EXTRACTED LENGTH:", len(extracted_text))

            if extracted_text.strip():
                try:
                    add_document_to_chroma(conv.id, extracted_text)
                except Exception:
                    pass

        return redirect("conversation_detail", conv_id=conv.id)


    # -----------------------------
    # RENDER PAGE
    # -----------------------------
    messages = conv.messages.order_by("timestamp")
    documents = conv.documents.order_by("-uploaded_at")
    upload_form = DocumentUploadForm()

    return render(
        request,
        "chat/conversation.html",
        {
            "conversation": conv,
            "messages": messages,
            "documents": documents,
            "upload_form": upload_form,
            "all_conversations": all_conversations,
        },
    )


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
