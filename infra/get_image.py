import sagemaker
from sagemaker.huggingface import get_huggingface_llm_image_uri
import boto3

session = boto3.Session(region_name="ap-south-1")
llm_image = get_huggingface_llm_image_uri(
  "huggingface",
  version="2.0.2"
)
print(llm_image)
