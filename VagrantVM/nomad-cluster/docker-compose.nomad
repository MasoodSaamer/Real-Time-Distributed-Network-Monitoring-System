job "docker-compose" {
  datacenters = ["dc1"]
  type = "batch" # Batch type job that runs once. Change to service type if you want it to be continously running

  group "compose-group" {
    task "docker-compose-task" {
      driver = "raw_exec"

      config {
        command = "/usr/local/bin/docker-compose"
        args    = ["-f", "/vagrant/vs-project/docker-compose.yml", "up", "-d", "--build"] # Path for the synched folder within Vagrant VM
      }

      resources {
        cpu    = 500 # CPU and memory allocation
        memory = 512
      }
    }
  }
}
