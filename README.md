# netics-oprec-module1-2026

Untuk penugasan modul 1 disini, saya akan menggunakan FastAPI + Uvicorn (Python) karena kemudahan (pip install dan selesai hehe). 

```python
from fastapi import FastAPI
from datetime import datetime
import time

app = FastAPI()
start_time = time.time()

@app.get("/health")
async def health():
    return {
        "nama": "Mikail Ibrahim Hakim",
        "nrp": "5025241046",
        "status": "UP",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - start_time
    }
```

Aplikasi diatas adalah REST API endpoint untuk `/health` maka dari itu perlu server yang dapat digunakan yaitu `uvicorn` . Uvicorn dijalankan dengan perintah `uvicorn main:app`. Dengan itu selanjutnya dijadikan docker image pada port 8000. (local testing)

Dilanjutkan dengan inisialisasi VPS dengan penginstallan `docker`,`nginx`,`python`. Inisialisasi ini juga membuat SSH private key dan public key agar GitHub Actions bisa terhubung ke VPS yang berada. 

```bash
ssh -i ~/.ssh/github_actions root@inivpssayamasjangandihack🥺
```

Setelah itu, setup secret pada github yaitu:
<img width="1015" height="345" alt="Pasted image 20260327182650" src="https://github.com/user-attachments/assets/547d53ec-a038-4f29-a3ed-b670ef677ebf" />


Selanjutnya untuk setup ansible perlu menggunakan playbook (disini juga menggunakan inventory agar tidak ada username/host yang terekspos). Default website nginx akan dihilangkan untuk memastikan server hanya untuk mengakses endpoint `/health`.

Urutan pelaksanaan ansible:
1. Download packages
2. Pull docker image terbaru
3. Stop container yang masih menyala
4. Menjalankan container terbaru
5. Konfigurasi nginx melalui template pada `src/ansible/templates`
6. Hapus default nginx website
7. Restart service nginx

```yml
---
- name: Deploy Health API
  hosts: vps
  become: true

  vars:
    image_name: "your_dockerhub_username/health-api:latest"
    container_name: "health-api"
    app_port: 8000

  tasks:
    - name: Install required packages
      apt:
        name:
          - docker.io
          - nginx
          - python3-pip
        state: present
        update_cache: true

    - name: Start and enable Docker
      service:
        name: docker
        state: started
        enabled: true

    - name: Pull latest Docker image
      community.docker.docker_image:
        name: "{{ image_name }}"
        source: pull
        force_source: true

    - name: Stop existing container
      community.docker.docker_container:
        name: "{{ container_name }}"
        state: absent
      ignore_errors: true

    - name: Run Docker container
      community.docker.docker_container:
        name: "{{ container_name }}"
        image: "{{ image_name }}"
        state: started
        restart_policy: always
        ports:
          - "{{ app_port }}:{{ app_port }}"

    - name: Configure Nginx reverse proxy
      template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/sites-available/health-api
        mode: '0644'

    - name: Enable Nginx site
      file:
        src: /etc/nginx/sites-available/health-api
        dest: /etc/nginx/sites-enabled/health-api
        state: link

    - name: Remove default Nginx site
      file:
        path: /etc/nginx/sites-enabled/default
        state: absent

    - name: Restart Nginx
      service:
        name: nginx
        state: restarted
        enabled: true
```

Untuk memastikan keamanan maka akan menggunakan ansible inventory seperti di bawah ini :
```ini
[vps]
your_vps_ip ansible_user=root ansible_ssh_private_key_file=~/.ssh/id_rsa
```

Setelah itu setting CI/CD workflow untuk:
1. Build dan push docker image
2. Setup server melalui Ansible

```yml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main

jobs:
  build-and-push:
    name: Build & Push Docker Image
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./src
          push: true
          tags: ${{ secrets.DOCKER_USERNAME }}/health-api:latest

  deploy:
    name: Deploy via Ansible
    runs-on: ubuntu-latest
    needs: build-and-push

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Ansible
        run: |
          pip install ansible
          ansible-galaxy collection install community.docker

      - name: Setup SSH key
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.VPS_SSH_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.VPS_HOST }} >> ~/.ssh/known_hosts

      - name: Update inventory with VPS IP
        run: |
          sed -i 's/your_vps_ip/${{ secrets.VPS_HOST }}/' src/ansible/inventory.ini

      - name: Update image name in playbook
        run: |
          sed -i 's/your_dockerhub_username/${{ secrets.DOCKER_USERNAME }}/' src/ansible/playbook.yml

      - name: Run Ansible Playbook
        run: |
          ansible-playbook -i src/ansible/inventory.ini src/ansible/playbook.yml

```

---
### AI Declaration
Penggunaan AI selama pengerjaan ini purely untuk referensi cloud server yang dapat saya manfaatkan (gratis), dan juga membantu debug, namun seluruh implementasi, troubleshooting, dan juga pemahaman konsep dilakukan secara mandiri (pls butuh oracle cloud 🥺🙏). 

