git clone https://github.com/chupino/monitorexamen.git monitor
cd monitor

docker build -t monitor .
if [ $? -eq 0 ]; then
    echo "contruida"
else
    echo "mal"
    exit 1
fi

docker run -dp 6666:5000 monitor
