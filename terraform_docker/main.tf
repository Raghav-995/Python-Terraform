
    terraform {
      required_providers {
        docker = {
          source  = "kreuzwerker/docker"
          version = "~> 2.0"
        }
      }
    }

    provider "docker" {}

    resource "docker_image" "example" {
      name         = "nginx:latest"
      keep_locally = true
    }

    resource "docker_container" "example" {
      name  = "raghav_1"
      image = docker_image.example.name
    ports {
      external = 80
      internal = 82
    }
    }
    