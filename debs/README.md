# Debian packages
To simplify installation of some dependencies we build needed packages
## Building Nginx Unit packages
Nginx Unit does not currently package for raspbian, so we need to build its packages ourselves. Below is the procedure we followed. It needs to be executed on the pi (or a raspbian container) and takes 20-30 minutes.
TODO: dockerize this package creation so we can make full releases.
```
debs='/home/pi/debs'
pushd $(mktemp --directory)
git clone https://github.com/nginx/unit
git checkout 1.22.0 # latest version
cd unit/pkg
sudo apt install -y php-dev libphp-embed python3.7-dev python3.8-dev golang libperl-dev ruby-dev ruby-rack openjdk-8-jdk-headless openjdk-8-jdk-headless openjdk-11-jdk-headless libpcre2-dev
make deb
cd debs
cp unit_*.deb unit-python3.7*.deb $debs
popd
