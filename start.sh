#!/bin/bash
while true
do
    echo "🚀 Avvio HomeStock Bot..."
    python main.py
    echo "⚠️ Il bot si è chiuso o è crashato!"
    echo "🔄 Riavvio automatico tra 5 secondi..."
    sleep 5
done