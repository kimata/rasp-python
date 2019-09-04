#!/usr/bin/env zsh

GATEWAY_IP=$(/sbin/ip route | awk '/default/ { print $3 }')
COUNT=5

count=$(ping -c $COUNT -q ${GATEWAY_IP} | grep 'received' | awk -F',' '{ print $2 }' | awk '{ print $1 }')

if [ "$count" = "0"]; then
    echo "Connectivity test failed. Let's try to reconnect to WiFi AP."
    /sbin/wpa_cli -i wlan0 reconfigure
else
    echo "Connectivity test passed. Packet(s) received: ${count}."
fi
