# Lab setup: ECS Fargate + Cloud Map

This is a **reconstructed deployment guide**, not exported infrastructure-as-code from the original experiment. It assumes basic AWS VPC, ECS and ECR knowledge. Prefer temporary resources in a dedicated test account.

## Prerequisites

- AWS account and permissions for VPC, ECR, ECS, IAM, Cloud Map and CloudWatch Logs
- AWS CLI v2 authenticated to the intended account; Docker available
- Region selected consistently (the original experiments used `us-east-1`)
- Two or more private subnets in a VPC, with the routing required for image pulls and logs

## 1. Networking

1. Create or select a VPC with DNS resolution and DNS hostnames enabled.
2. Create private subnets for Fargate workloads. `awsvpc` networking gives each task its own ENI and private IP.
3. Provide private-subnet connectivity to Amazon ECR, S3 (for ECR layers), CloudWatch Logs and other required AWS endpoints via appropriate VPC endpoints or outbound egress (e.g. NAT). Review regional endpoint requirements and associated costs.
4. Create **Orders SG** and **Payments SG**. Allow **inbound TCP 5000 to Payments only from Orders SG**. Permit appropriate outbound traffic from Orders. The Payments endpoint need not be internet-facing.
5. Use restrictive ingress and egress rules suited to your test environment. Run probes from inside the VPC (for instance through ECS Exec).

## 2. Container images

From the repository root, build both images for the target Fargate CPU architecture:

```bash
docker build -t ecs-orders:lab apps/orders
docker build -t ecs-payments:lab apps/payments
```

Create two private Amazon ECR repositories (`ecs-orders` and `ecs-payments`), authenticate Docker to your ECR registry, tag images and push them. Example for one image, after setting your own placeholders:

```bash
AWS_REGION=us-east-1
ACCOUNT_ID=<your-aws-account-id>
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
docker tag ecs-orders:lab "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ecs-orders:lab"
docker push "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ecs-orders:lab"
```

Repeat tagging/pushing for Payments, substituting `ecs-payments`. Do not commit account identifiers or credentials to the repository.

## 3. Cloud Map

1. Create a **private DNS namespace** named `lab.internal` associated with the lab VPC.
2. Create a service named `payments`, using a DNS **A** record, **MULTIVALUE** routing and a **10-second TTL** (matching the original experiment).
3. In ECS, configure the Payments service's service discovery integration to register its running task IPs with that Cloud Map service.
4. From workloads in the VPC, the discovery name becomes `payments.lab.internal`.

Note: DNS cache behavior, registration timing and health integration affect when changes become visible. Cloud Map is **not** a request-by-request HTTP load balancer.

## 4. ECS

1. Create an ECS cluster, e.g. `microservices-lab`.
2. Configure an ECS task execution role with permissions needed for ECR pulls and CloudWatch log delivery.
3. Create **two Fargate task definitions** with `awsvpc`, appropriate CPU/memory, container ports **4000** (Orders) and **5000** (Payments), and CloudWatch log configuration. Use the image URIs from your own ECR repositories.
4. Optionally pass Orders `PAYMENTS_URL=http://payments.lab.internal:5000`; this is already the application's default.
5. Create an **Orders** ECS service in your private subnets with desired count **1** and the Orders security group.
6. Create a **Payments** ECS service in your private subnets with desired count **3**, Payments security group, and the Cloud Map service-discovery registration from step 3.
7. Verify all tasks are RUNNING and that application-level health checks respond. ECS RUNNING is not by itself a guarantee that your application is ready.
8. For diagnostics, enable ECS Exec with a compatible task role, execute-command settings, and required Systems Manager Session Manager permissions and connectivity. Alternately, launch a temporary diagnostic workload inside the same VPC.

### Example testing from an Orders task

The minimal app image contains Python and `requests`, but does **not** include `curl` by default. From ECS Exec, run:

```bash
python -c 'import socket; print(socket.gethostbyname_ex("payments.lab.internal"))'
python -c 'import requests; r=requests.get("http://payments.lab.internal:5000/payment", timeout=5); print(r.status_code, r.text)'
```

To use the repository's scripts, copy or bake them into a temporary diagnostic image or run them from a similarly configured VPC diagnostic task. The standard app containers do not include the `scripts/` folder.

## 5. Run the experiments

See [experiments.md](experiments.md) and compare with [results.md](results.md).

## 6. Cleanup

After recording results:

1. Scale Orders and Payments ECS services to zero and delete the services.
2. Remove Cloud Map service registrations/service and private DNS namespace when no longer used.
3. Delete the lab ECS task definitions if desired, plus CloudWatch log groups.
4. Delete ECR images/repositories if dedicated to the lab.
5. Delete lab VPC endpoints, NAT gateways and networking resources **only if** created exclusively for this lab.
6. Check billing and remaining ENIs/resources. ECS, NAT, VPC endpoints, logs and Cloud Map may incur charges.

Do not use these steps to delete shared production infrastructure.
