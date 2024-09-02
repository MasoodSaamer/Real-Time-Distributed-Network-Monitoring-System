job "docker-compose" {
  datacenters = ["dc1"]
  type = "batch"

  group "compose-group" {
    task "docker-compose-task" {
      driver = "raw_exec"

      config {
        command = "/usr/local/bin/docker-compose"
        args    = ["-f", "/vagrant/vs-project/docker-compose.yml", "up", "-d", "--build"]
      }

      resources {
        cpu    = 500
        memory = 512
      }
    }
  }
}
