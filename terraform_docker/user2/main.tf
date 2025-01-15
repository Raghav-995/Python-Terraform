
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
      name         = "nginx"
      keep_locally = true
    }

    resource "docker_container" "example" {
      name  = "raghav_container_2"
      image = docker_image.example.name
    ports {
      external = 8084
      internal = 80
    }
    }
    