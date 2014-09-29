# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

$priv_script = <<SCRIPT

apt-get update
apt-get install -y ca-certificates apt-transport-https

cat >/usr/share/ca-certificates/weasyl.crt <<CERT
-----BEGIN CERTIFICATE-----
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
ciUxyHpFoNm83jJXXC++k8/svTSvaHE=
-----END CERTIFICATE-----
CERT

echo 'weasyl.crt' >> /etc/ca-certificates.conf

update-ca-certificates

echo >/etc/apt/sources.list.d/nodesource.list \
    'deb https://deb.nodesource.com/node wheezy main'
echo >/etc/apt/sources.list.d/weasyl.list \
    'deb http://apt.i.weasyl.com/repos/apt/debian wheezy main'

wget -O- https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
wget -O- https://deploy.i.weasyl.com/weykent-key.asc | apt-key add -

apt-get update
apt-mark hold grub-pc
apt-get -y upgrade

apt-get -y install \
    python3.4-dev python3.4-venv imagemagick-6.8.9 libreadline-dev \
    git-core postgresql postgresql-contrib-9.1 libpq-dev memcached nginx \
    libxml2-dev libxslt-dev pkg-config npm ruby-sass openssh-client openssh-server

sudo -u postgres psql -c 'DROP DATABASE weasyl'
sudo -u postgres psql -c 'DROP USER vagrant'
sudo -u postgres createuser -drs vagrant
sudo -u postgres createdb -E UTF8 -O vagrant weasyl
wget -O- https://deploy.i.weasyl.com/weasyl-latest.sql.xz \
    | xzcat | sudo -u vagrant psql weasyl

openssl req -subj '/CN=lo3.weasyl.com' -nodes -new -newkey rsa:2048 \
    -keyout /etc/ssl/private/weasyl3.key.pem -out /tmp/weasyl3.req.pem
openssl x509 -req -days 3650 -in /tmp/weasyl3.req.pem \
    -signkey /etc/ssl/private/weasyl3.key.pem -out /etc/ssl/private/weasyl3.crt.pem

cat >/etc/nginx/sites-available/weasyl <<NGINX

server {
    listen 8080;
    listen 8443 ssl;

    ssl on;
    ssl_certificate /etc/ssl/private/weasyl3.crt.pem;
    ssl_certificate_key /etc/ssl/private/weasyl3.key.pem;

    server_name lo3.weasyl.com;

    rewrite "^(/static/(submission|character)/../../../../../../)(.+)-(.+)\$" \\$1\\$4 break;

    location /static {
        root /home/vagrant/weasyl3/weasyl;
        try_files \\$uri @proxy;
    }

    location / {
        proxy_pass http://127.0.0.1:8880;
        if (\\$request_method = HEAD) {
            gzip off;
        }

        proxy_redirect off;
        proxy_set_header X-Forwarded-Proto \\$scheme;
        proxy_set_header Host \\$http_host;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        client_max_body_size 30m;
        client_body_buffer_size 128k;
        proxy_connect_timeout 10;
        proxy_send_timeout 30;
        proxy_read_timeout 30;
        proxy_buffers 32 4k;
    }

    location @proxy {
        proxy_pass https://www.weasyl.com;
    }
}

NGINX
ln -fs /etc/nginx/sites-available/weasyl /etc/nginx/sites-enabled
/etc/init.d/nginx restart

SCRIPT


$unpriv_script = <<SCRIPT

ln -s /vagrant ~/weasyl3
cd ~/weasyl3
sed -e 's,^weasyl.static_root = /path/to/your/weasyl-old/checkout$,weasyl.static_root = /home/vagrant/weasyl3/weasyl/static,' <etc/development.ini.example >etc/development.ini
make install-libweasyl PYVENV=pyvenv-3.4

SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "weasyl-debian76"
  config.vm.box_url = "https://deploy.i.weasyl.com/weasyl-debian76.box"
  config.vm.box_download_insecure = true
  config.vm.box_download_checksum = "58c6db2da40bc22bd03347f12af4c8ba06a7e1f73192d3202bae1071ef948cf4"
  config.vm.box_download_checksum_type = "sha256"
  config.vm.provision :shell, :privileged => true, :inline => $priv_script
  config.vm.provision :shell, :privileged => false, :inline => $unpriv_script
  config.vm.network :forwarded_port, host: 28443, guest: 8443
end
