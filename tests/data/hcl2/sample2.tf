resource "aws_cloudwatch_log_group" "drone_server" {
  name = "drone/server"
  tags = {
    Name = var.fqdn
  }
}

data "aws_caller_identity" "current" {}

locals {
  ssm_root = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter"
}



resource "aws_iam_role_policy" "ci_agent_ecs" {
  role   = aws_iam_role.ci_agent_ecs_task.name
  policy = templatefile("${path.module}/templates/drone-ecs.json", { server_log_group_arn = var.agent_log_group_arn, agent_log_group_arn = aws_cloudwatch_log_group.drone_server.arn, })

}

resource "aws_security_group" "ci_agent_app" {
  description = "Restrict access to application server."
  vpc_id      = var.vpc_id
  name        = "ci-server-task-sg"
}

resource "aws_security_group_rule" "ci_agent_app_egress" {
  type        = "egress"
  description = "RDP c"
  depends_on  = [aws_security_group.ci_agent_app]
  from_port   = 0
  to_port     = 0
  protocol    = "-1"

  cidr_blocks = [
    "0.0.0.0/0",
  ]

  security_group_id = aws_security_group.ci_agent_app.id
}

resource "aws_security_group_rule" "ci_agent_app_ingress" {
  type        = "ingress"
  description = "Drone CI/CD build agents to access"
  depends_on  = [aws_security_group.ci_agent_app]
  protocol    = "tcp"
  from_port   = var.build_agent_port
  to_port     = var.build_agent_port

  source_security_group_id = var.cluster_instance_security_group_id
  security_group_id        = aws_security_group.ci_agent_app.id
}

resource "aws_iam_role" "ci_agent_ecs_task" {
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}