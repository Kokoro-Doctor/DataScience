from __future__ import annotations
import base64
import os
from typing import List
from datetime import datetime
import streamlit as st
import pandas as pd
import shutil
import glob

# LangChain + Gemini
from langchain.chains import TransformChain
from langchain_core.messages import HumanMessage
from langchain import globals
from langchain_core.runnables import chain
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

# API Key
from keys import GOOGLE_API_KEY
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
globals.set_debug(False)


# ----------------- Custom CSS Loader -----------------
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("styles.css")


# ----------------- Pydantic Models -----------------
class MedicationItem(BaseModel):
    name: str
    dosage: str
    frequency: str
    duration: str


class PrescriptionInformations(BaseModel):
    patient_name: str = Field(description="Patient's name")
    patient_age: int = Field(description="Patient's age")
    patient_gender: str = Field(description="Patient's gender")
    doctor_name: str = Field(description="Doctor's name")
    doctor_license: str = Field(description="Doctor's license number")
    prescription_date: str = Field(description="Date of the prescription (YYYY-MM-DD)")
    medications: List[MedicationItem] = []
    additional_notes: str = Field(description="Additional notes or instructions")


# ----------------- Image Encoder -----------------
def load_images(inputs: dict) -> dict:
    image_paths = inputs["image_paths"]

    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    images_base64 = [encode_image(image_path) for image_path in image_paths]
    return {"images": images_base64}


load_images_chain = TransformChain(
    input_variables=["image_paths"],
    output_variables=["images"],
    transform=load_images,
)


# ----------------- Gemini Model -----------------
parser = JsonOutputParser(pydantic_object=PrescriptionInformations)


@chain
def image_model(inputs: dict) -> str | list[str] | dict:
    """Invoke Gemini model with images and prompt."""
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.environ["GOOGLE_API_KEY"]
    )

    image_urls = [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
        for img in inputs["images"]
    ]

    prompt = """
    You are an expert medical transcriptionist specializing in deciphering and accurately
    transcribing handwritten medical prescriptions. 

    Extract:
    - Patient's full name, age, gender
    - Doctor's name & license number
    - Prescription date (YYYY-MM-DD)
    - Medications (name, dosage, frequency, duration)
    - Additional notes

    Return a clean JSON only.
    """

    msg = model.invoke(
        [HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "text", "text": parser.get_format_instructions()},
                *image_urls,
            ]
        )]
    )
    return msg.content


# ----------------- Chain Runner -----------------
def get_prescription_informations(image_paths: List[str]) -> dict:
    vision_prompt = """
    Extract prescription details clearly. 
    If any field is missing, leave it empty.
    """
    vision_chain = load_images_chain | image_model | parser
    return vision_chain.invoke({"image_paths": image_paths, "prompt": vision_prompt})


# ----------------- Streamlit App -----------------
def main():
    st.title("📋 Medical Prescription Parsing (Gemini)")

    uploaded_file = st.file_uploader("Upload a Prescription image", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = uploaded_file.name.split(".")[0].replace(" ", "_")
        output_folder = os.path.join(".", f"Check_{filename}_{timestamp}")
        os.makedirs(output_folder, exist_ok=True)

        check_path = os.path.join(output_folder, uploaded_file.name)
        with open(check_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.expander("Prescription Image", expanded=False):
            st.image(uploaded_file, caption="Uploaded Prescription Image.", use_column_width=True)

        with st.spinner("Processing Prescription with Gemini..."):
            final_result = get_prescription_informations([check_path])

            # Display results in table
            if "additional_notes" in final_result:
                additional_notes = final_result["additional_notes"]
                if isinstance(additional_notes, list):
                    formatted_notes = "<br> ".join(additional_notes)
                else:
                    formatted_notes = additional_notes.replace("\n", "<br> ")
                final_result["additional_notes"] = f"<ul><li>{formatted_notes}</li></ul>"

            data = [(key, final_result[key]) for key in final_result if key != "medications"]
            df = pd.DataFrame(data, columns=["Field", "Value"])

            st.write(df.to_html(classes="custom-table", index=False, escape=False), unsafe_allow_html=True)

            if "medications" in final_result and final_result["medications"]:
                medications_df = pd.DataFrame(final_result["medications"])
                st.subheader("Medications")
                st.write(medications_df.to_html(classes="custom-table", index=False, escape=False), unsafe_allow_html=True)

        shutil.rmtree(output_folder, ignore_errors=True)


if __name__ == "__main__":
    main()
