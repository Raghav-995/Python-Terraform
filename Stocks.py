# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt

# # Seed for reproducibility
# np.random.seed(42)

# # Generate dates
# dates = pd.date_range(start="2023-10-01", periods=30, freq='D')

# # Simulate stock prices
# initial_price = 100
# price_changes = np.random.normal(loc=0, scale=2, size=len(dates))  # daily price changes
# prices = initial_price + np.cumsum(price_changes)  # cumulative sum to get price series

# # Create DataFrame
# stock_data = pd.DataFrame(data={'Date': dates, 'Price': prices})
# stock_data.set_index('Date', inplace=True)

# # Calculate daily returns and moving averages
# stock_data['Daily Return'] = stock_data['Price'].pct_change()
# stock_data['30 Day MA'] = stock_data['Price'].rolling(window=30).mean()

# # Plotting
# plt.figure(figsize=(14, 7))

# # Stock price plot
# plt.subplot(3, 1, 1)
# plt.plot(stock_data['Price'], label='Stock Price', color='blue')
# plt.plot(stock_data['30 Day MA'], label='30 Day Moving Average', color='orange', linestyle='--')
# plt.title('Stock Price Over Time')
# plt.ylabel('Price ($)')
# plt.legend()

# # Daily return plot
# plt.subplot(3, 1, 2)
# plt.plot(stock_data['Daily Return'], label='Daily Return', color='green')
# plt.title('Daily Returns Over Time')
# plt.ylabel('Return (%)')
# plt.axhline(0, color='black', linewidth=0.5, linestyle='--')
# plt.legend()

# # Histogram of daily returns
# plt.subplot(3, 1, 3)
# plt.hist(stock_data['Daily Return'].dropna(), bins=10, alpha=0.7, color='purple')
# plt.title('Histogram of Daily Returns')
# plt.xlabel('Return (%)')
# plt.ylabel('Frequency')

# plt.tight_layout()
# plt.show()
import os
import json
from python_terraform import Terraform

WORKSPACES_FILE = "workspaces.json"  # File to track workspaces and containers


def load_workspaces():
    """Load existing workspaces from the JSON file."""
    if os.path.exists(WORKSPACES_FILE):
        with open(WORKSPACES_FILE, "r") as file:
            return json.load(file)
    return {}


def save_workspaces(workspaces):
    """Save workspaces and their containers to the JSON file."""
    with open(WORKSPACES_FILE, "w") as file:
        json.dump(workspaces, file, indent=4)


def list_containers():
    """List all available Docker containers."""
    containers = os.popen("docker ps -a --format '{{.Names}}'").read().strip().split("\n")
    return [container.strip() for container in containers if container]  # Ensure no empty strings


import subprocess

def destroy_selected_container():
    """Allow the user to select a container and destroy it."""
    containers = list_containers()  # Assuming list_containers() returns a list of container names
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
            print(container_name)
            # Check if the container exists
            inspect_result = subprocess.run(
                ["docker", "inspect", container_name],
                capture_output=True,
                text=True
            )
            if inspect_result.returncode == 0:
                # Stop the container
                stop_result = subprocess.run(
                    ["docker", "stop", container_name],
                    capture_output=True,
                    text=True
                )
                if stop_result.returncode == 0:
                    print(f"Container {container_name} stopped successfully.")

                    # Remove the container
                    rm_result = subprocess.run(
                        ["docker", "rm", container_name],
                        capture_output=True,
                        text=True
                    )
                    if rm_result.returncode == 0:
                        print(f"Container {container_name} has been destroyed.")
                    else:
                        print(f"Error removing container {container_name}: {rm_result.stderr.strip()}")
                else:
                    print(f"Error stopping container {container_name}: {stop_result.stderr.strip()}")
            else:
                print(f"Error: Container {container_name} does not exist.")
        else:
            print("Invalid choice.")
    except ValueError:
        print("Please enter a valid number.")
    except Exception as e:
        print(f"An error occurred: {e}")



def docker_options():
    """Provide options for creating or destroying Docker containers."""
    print("Docker Options:")
    print("1. Create a new container")
    print("2. Destroy an existing container")
    choice = input("Enter your choice (1/2): ")

    if choice == "1":
        print("Docker container creation is not yet implemented in this version.")
    elif choice == "2":
        destroy_selected_container()
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    print("Choose infrastructure to create:")
    print("1. AWS EC2 Instance")
    print("2. Docker Container")
    print("3. OpenStack Instance")
    print("4. VMware Instance")

    choice = input("Enter your choice (1/2/3/4): ")

    if choice == "2":
        docker_options()
    else:
        print("Selected option is not implemented yet.")
