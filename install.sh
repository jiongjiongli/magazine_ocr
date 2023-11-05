echo 'Start install poppler-utils and imagemagick...'
apt-get install -y poppler-utils imagemagick

sed -i -e 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml

echo 'Start install pip packages...'
pip install -r requirements.txt
