import os
import json
from python_terraform import Terraform

WORKSPACES_FILE = "workspaces.json"  # File to track workspaces and containers


def load_workspaces():
    """
    Load existing workspaces from the JSON file.
    """
    if os.path.exists(WORKSPACES_FILE):
        with open(WORKSPACES_FILE, "r") as file:
            return json.load(file)
    return {}

def save_workspaces(workspaces):
    """
    Save workspaces and their containers to the JSON file.
    """
    with open(WORKSPACES_FILE, "w") as file:
        json.dump(workspaces, file, indent=4)

def setup_terraform_directory(directory, config):
    """
    Sets up the Terraform working directory by writing the configuration to main.tf.
    """
    
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, "main.tf"), "w") as tf_file:
        tf_file.write(config)

def initialize_terraform(directory):
    """
    Initializes the Terraform working directory.
    """
    terraform = Terraform(working_dir=directory)
    print("Initializing Terraform...")
    return_code, stdout, stderr = terraform.init()
    if return_code != 0:
        print(stderr)
        raise Exception("Terraform initialization failed.")
    print(stdout)
    return terraform

def apply_terraform(terraform):
    """
    Applies the Terraform configuration.
    """
    print("Applying Terraform configuration...")
    return_code, stdout, stderr = terraform.apply(skip_plan=True)
    if return_code != 0:
        print(stderr)
        raise Exception("Terraform apply failed.")
    print(stdout)

def destroy_terraform(terraform):
    """
    Destroys the Terraform-managed infrastructure.
    """
    destroy = input("Do you want to destroy the infrastructure? (yes/no): ").lower()
    if destroy == "yes":
        print("Destroying Terraform infrastructure...")
        return_code, stdout, stderr = terraform.destroy(auto_approve=True)
        print(stdout)
        
def list_containers():
    """List all available Docker containers."""
    containers = os.popen("docker ps -a --format '{{.Names}}'").read().strip().split("\n")
    return [container.strip() for container in containers if container]  # Ensure no empty strings

def destroy_selected_container():
    """Allow the user to select a container and destroy it."""
    containers = list_containers()
    if not containers:
        print("No containers found.")
        return

    print("Available containers:")
    for idx, container in enumerate(containers, 1):
        print(f"{idx}. {container}")

    try:
        choice = int(input("Enter the number of the container to destroy: ")) - 1
        if 0 <= choice < len(containers):
            container = containers[choice].strip()  # Remove any surrounding whitespace
            container_name = eval(container)
            os.system(f"docker stop {container_name}")
            os.system(f"docker rm {container_name}")
            print(f"Container {container_name} has been destroyed.")
        else:
            print("Invalid choice.")
    except ValueError:
        print("Please enter a valid number.")

        
def create_docker_container(image, container_name, ports, workspace):
    """
    Creates a Docker container using Terraform, ensuring the container does not already exist.
    """
    # Ensure the workspace exists
    create_workspace(workspace)

    terraform_dir = f"./terraform_docker/{workspace}"

    # Generate Terraform configuration with user inputs
    port_mappings = "\n".join(
        [
            f"""    ports {{
      external = {p.split(":")[0]}
      internal = {p.split(":")[1]}
    }}"""
            for p in ports
        ]
    )

    terraform_config = f"""
    terraform {{
      required_providers {{
        docker = {{
          source  = "kreuzwerker/docker"
          version = "~> 2.0"
        }}
      }}
    }}

    provider "docker" {{}}

    resource "docker_image" "example" {{
      name         = "{image}"
      keep_locally = true
    }}

    resource "docker_container" "example" {{
      name  = "{container_name}"
      image = docker_image.example.name
{port_mappings}
    }}
    """
    setup_terraform_directory(terraform_dir, terraform_config)

    # Check for existing Docker container and image
    existing_containers = os.popen("docker ps -a --format '{{.Names}}'").read().splitlines()
    if container_name in existing_containers:
        print(f"Container '{container_name}' already exists. Destroying it...")
        os.system(f"docker stop {container_name}")
        os.system(f"docker rm {container_name}")

    existing_images = os.popen("docker images --format '{{.Repository}}'").read().splitlines()
    if image.split(":")[0] in existing_images:
        print(f"Image '{image}' already exists. Skipping image pull...")
    else:
        print(f"Image '{image}' does not exist locally. It will be pulled during Terraform apply.")

    terraform = initialize_terraform(terraform_dir)
    apply_terraform(terraform)
    destroy_terraform(terraform)


    # Save the container to the workspace
    workspaces = load_workspaces()
    if container_name not in workspaces[workspace]:
        workspaces[workspace].append(container_name)
        save_workspaces(workspaces)
    else:
        print(f"Container '{container_name}' is already in the workspace.")

def create_workspace(workspace_name):
    """
    Ensures a workspace exists. If not, creates a new one.
    """
    workspaces = load_workspaces()
    if workspace_name not in workspaces:
        workspaces[workspace_name] = []
        save_workspaces(workspaces)
        print(f"Workspace '{workspace_name}' created.")
    else:
        print(f"Workspace '{workspace_name}' already exists.")
        
def docker_options():
    """Provide options for creating or destroying Docker containers."""
    print("Docker Options:")
    print("1. Create a new container")
    print("2. Destroy an existing container")
    choice = input("Enter your choice (1/2): ")

    if choice == "1":
        workspace_name = input("Enter the workspace name: ")
        image = input("Enter Docker image (e.g., nginx:latest): ")
        container_name = input("Enter container name: ")
        ports_input = input("Enter port mappings (format: external:internal, e.g., 8080:80,443:443): ")
        ports = [p.strip() for p in ports_input.split(",") if p.strip()]
        create_docker_container(image, container_name, ports, workspace_name)
    elif choice == "2":
        destroy_selected_container()
    else:
        print("Invalid choice.")

def create_aws_instance(region, ami, instance_type, name):
    """
    Creates an AWS EC2 instance using Terraform.
    """
    terraform_dir = "./terraform_aws"
    terraform_config = f"""
    provider "aws" {{
      region = "{region}"
    }}

    resource "aws_instance" "example" {{
      ami           = "{ami}"
      instance_type = "{instance_type}"

      tags = {{
        Name = "{name}"
      }}
    }}
    """
    setup_terraform_directory(terraform_dir, terraform_config)
    terraform = initialize_terraform(terraform_dir)
    apply_terraform(terraform)

def create_openstack_instance(auth_url, username, password, tenant_name, flavor, image):
    """
    Creates an OpenStack instance using Terraform.
    """
    terraform_dir = "./terraform_openstack"
    terraform_config = f"""
    provider "openstack" {{
      auth_url    = "{auth_url}"
      username    = "{username}"
      password    = "{password}"
      tenant_name = "{tenant_name}"
    }}

    resource "openstack_compute_instance_v2" "example" {{
      name       = "example-instance"
      flavor_id  = "{flavor}"
      image_id   = "{image}"
    }}
    """
    setup_terraform_directory(terraform_dir, terraform_config)
    terraform = initialize_terraform(terraform_dir)
    apply_terraform(terraform)

def create_vmware_instance(vsphere_server, username, password, datacenter, folder, resource_pool, vm_template):
    """
    Creates a VMware instance using Terraform.
    """
    terraform_dir = "./terraform_vmware"
    terraform_config = f"""
    provider "vsphere" {{
      user           = "{username}"
      password       = "{password}"
      server         = "{vsphere_server}"
      allow_unverified_ssl = true
    }}

    data "vsphere_datacenter" "dc" {{
      name = "{datacenter}"
    }}

    data "vsphere_folder" "vm_folder" {{
      path = "{folder}"
      datacenter_id = data.vsphere_datacenter.dc.id
    }}

    resource "vsphere_virtual_machine" "vm" {{
      name             = "example-vm"
      resource_pool_id = "{resource_pool}"
      folder           = data.vsphere_folder.vm_folder.id
      template         = "{vm_template}"
    }}
    """
    setup_terraform_directory(terraform_dir, terraform_config)
    terraform = initialize_terraform(terraform_dir)
    apply_terraform(terraform)

if __name__ == "__main__":
    print("Choose infrastructure to create:")
    print("1. AWS EC2 Instance")
    print("2. Docker Container")
    print("3. OpenStack Instance")
    print("4. VMware Instance")

    choice = input("Enter your choice (1/2/3/4): ")

    if choice == "1":
        region = input("Enter AWS region: ")
        ami = input("Enter AMI ID: ")
        instance_type = input("Enter instance type: ")
        name = input("Enter instance name: ")
        create_aws_instance(region, ami, instance_type, name)
    elif choice == "2":
       docker_options()
    elif choice == "3":
        auth_url = input("Enter OpenStack auth URL: ")
        username = input("Enter OpenStack username: ")
        password = input("Enter OpenStack password: ")
        tenant_name = input("Enter OpenStack tenant name: ")
        flavor = input("Enter OpenStack flavor ID: ")
        image = input("Enter OpenStack image ID: ")
        create_openstack_instance(auth_url, username, password, tenant_name, flavor, image)
    elif choice == "4":
        vsphere_server = input("Enter VMware vSphere server: ")
        username = input("Enter VMware username: ")
        password = input("Enter VMware password: ")
        datacenter = input("Enter VMware datacenter: ")
        folder = input("Enter VMware folder: ")
        resource_pool = input("Enter VMware resource pool: ")
        vm_template = input("Enter VMware VM template ID: ")
        create_vmware_instance(vsphere_server, username, password, datacenter, folder, resource_pool, vm_template)
    else:
        print("Invalid choice.")
