output "backend_public_ip" {
  description = "Public IP of the backend EC2 server"
  value       = aws_instance.backend_server.public_ip
}

output "backend_ssh_command" {
  description = "Command to SSH into the server if a key was provided"
  value       = "ssh -i YOUR_KEY.pem ubuntu@${aws_instance.backend_server.public_ip}"
}

output "api_url" {
  description = "The base URL for the FastAPI backend"
  value       = "http://${aws_instance.backend_server.public_ip}:8000"
}

output "frontend_url" {
  description = "The base URL for the Next.js frontend (if hosted on the same server)"
  value       = "http://${aws_instance.backend_server.public_ip}:3001"
}

output "backend_iam_role_arn" {
  description = "IAM Role ARN attached to the backend server"
  value       = aws_iam_role.backend_role.arn
}
