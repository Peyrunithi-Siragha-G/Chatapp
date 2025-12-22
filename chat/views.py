from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
from django.template.loader import render_to_string
from .ai_model import generate_ai_reply, generate_ai_title
from .models import Conversation, Message, Document
from .forms import SignUpForm, DocumentUploadForm

from .chroma_manager import add_document
text = extract_text_from_file(file_path)
add_document(conversation.id, text)

from .chroma_manager import query_document

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
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

        from django.contrib.auth.models import User
        if password1 != password2:
            return render(request, "chat/signup.html", {"error": "Passwords do not match"})

        if User.objects.filter(username=username).exists():
            return render(request, "chat/signup.html", {"error": "Username already exists"})

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        return redirect("conversations_list")

    return render(request, "chat/signup.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def conversations_list(request):
    conversations = Conversation.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "chat/conversations.html", {
        "all_conversations": conversations,
        "conversation": None,
    })


@login_required
def conversation_detail(request, conv_id=None):
    all_conversations = Conversation.objects.filter(user=request.user).order_by("-created_at")

    if conv_id is None:
        conv = Conversation.objects.create(user=request.user, title="New Chat")
        return redirect("conversation_detail", conv_id=conv.id)

    conv = get_object_or_404(Conversation, pk=conv_id, user=request.user)

    # User message
    if request.method == "POST" and "text" in request.POST:
        text = request.POST.get("text")

        if text:
            Message.objects.create(
                conversation=conv,
                user=request.user,
                text=text,
                is_bot=False
            )

            if conv.title == "New Chat":
                conv.title = generate_ai_title(text)
                conv.save()

            # Chroma search
            from .chroma_manager import search_relevant_text
            context = search_relevant_text(text)

            full_prompt = f"Relevant document info:\n{context}\n\nUser question: {text}"
            relevant_chunks = query_document(conversation.id, user_message)

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
            if not relevant_chunks:
                ai_response = "No relevant information found in the uploaded document."

            Message.objects.create(
                conversation=conv,
                user=request.user,
                text=ai_response,
                is_bot=True
            )

        return redirect("conversation_detail", conv_id=conv.id)

    # Upload document
    if request.method == "POST" and "file" in request.FILES:
        upload_form = DocumentUploadForm(request.POST, request.FILES)

        if upload_form.is_valid():
            doc = upload_form.save(commit=False)
            doc.user = request.user
            doc.conversation = conv
            doc.save()

            from .analyzer import extract_text_from_file
            from .chroma_manager import add_document_to_chroma

            extracted = extract_text_from_file(doc.file.path)
            if extracted.strip():
                add_document_to_chroma(doc.id, extracted)

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


def messages_partial(request, conv_id):
    conv = get_object_or_404(Conversation, pk=conv_id)
    messages = conv.messages.order_by("timestamp")
    html = render_to_string("chat/messages_list.html", {"messages": messages})
    return JsonResponse({"html": html})
