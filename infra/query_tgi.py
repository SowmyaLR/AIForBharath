import boto3

try:
    ssm = boto3.client('ssm', region_name='ap-south-1')
    paginator = ssm.get_paginator('get_parameters_by_path')
    
    found = False
    for page in paginator.paginate(Path='/aws/service/sagemaker/frameworks/huggingface-pytorch-tgi-inference/', Recursive=True):
        if 'Parameters' in page:
            for param in page['Parameters']:
                if 'gpu' in param['Name'] and 'ubuntu22' in param['Name']:
                    print(f"FOUND: {param['Value']}")
                    found = True
                    
    if not found:
        print("No TGI parameters found.")
                
except Exception as e:
    print(f"Error: {e}")
