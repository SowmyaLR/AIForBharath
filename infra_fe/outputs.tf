output "amplify_app_id" {
  description = "The ID of the Amplify App"
  value       = aws_amplify_app.vaidya.id
}

output "amplify_url" {
  description = "The default URL of the Amplify App"
  value       = "https://main.${aws_amplify_app.vaidya.default_domain}"
}
