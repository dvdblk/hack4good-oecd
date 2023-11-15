import streamlit as st
from dotenv import load_dotenv
import base64


@st.cache_data
def displayPDF(uploaded_file):
    # Read file as bytes:
    bytes_data = uploaded_file.getvalue()

    # Convert to utf-8
    base64_pdf = base64.b64encode(bytes_data).decode("utf-8")

    # Embed PDF in HTML
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="320" type="application/pdf"></iframe>'

    # Display file
    st.markdown(pdf_display, unsafe_allow_html=True)


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    st.set_page_config(page_title="OECD Policy Explorer 🔎", page_icon="💼")

    st.header("Results")
    chat_input = st.text_input("Ask a question here")

    chat_question_choice_pressed = st.button("Examples")

    if chat_question_choice_pressed:
        selected_question = st.selectbox(
            "Select a question", ["What are the skills mentioned in this document?"]
        )

    # Create a sidebar for docs manager
    with st.sidebar:
        st.subheader("PDF Documents")
        # Store the uploaded PDF documents in a list
        raw_pdf_documents = st.file_uploader(
            "Upload your PDF document(s)",
            type="pdf",
            accept_multiple_files=True,
            help="Here you can upload any policy document(s) in PDF format.",
        )
        if st.button("Upload PDF(s)"):
            with st.spinner("Processing..."):
                # TODO: Identify if the PDF documents are new (hash the first few and last pages + page count)
                # TODO: Identify the language of the documents (load with pypdf2 and use langdetect)

                # Call extract API here
                st.write("Done!")
                st.write("Here are the results:")
                st.write(len(raw_pdf_documents))
                displayPDF(raw_pdf_documents[0])
