resource "google_compute_instance" "default" {
  name         = "cointrade"
  machine_type = "e2-medium"
  zone         = "asia-northeast3-a"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts"
    }
  }

  metadata_startup_script = <<-EOF
    sudo apt-get update
    sudo apt-get install -y git
    cd /home/$USER
    git clone https://github.com/zangwoo-jeon/AutoTrade_bithumb.git
    sudo apt update
    sudo apt-get install -y python3-pip
    pip install pybithumb
    EOF
    
  network_interface {
    network = "default"
    access_config {}
  }
}
