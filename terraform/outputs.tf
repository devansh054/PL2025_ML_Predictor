output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.pl_predictor_vpc.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public_subnets[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private_subnets[*].id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.pl_predictor_cluster.name
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.pl_predictor_alb.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.pl_predictor_alb.zone_id
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.pl_predictor_db.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_replication_group.pl_predictor_redis.primary_endpoint_address
  sensitive   = true
}
