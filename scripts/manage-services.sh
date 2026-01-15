#!/bin/bash
# Manage Podman container services

ACTION=$1

# Check if podman is available
if ! command -v podman &> /dev/null; then
    echo "Error: Podman not found"
    echo "Please install Podman:"
    echo "  - macOS: brew install podman"
    echo "  - Linux: sudo apt install podman (Ubuntu/Debian) or sudo dnf install podman (Fedora/RHEL)"
    exit 1
fi

case "$ACTION" in
    stop)
        echo "Stopping container services..."
        podman stop huali-mysql huali-redis 2>/dev/null || true
        echo "[OK] Container services stopped"
        ;;
    
    restart)
        echo "Restarting container services..."
        if podman restart huali-mysql huali-redis 2>/dev/null; then
            echo "[OK] Container services restarted"
        else
            echo "[ERROR] Failed to restart containers. Please start them first with: make services-up"
            exit 1
        fi
        ;;
    
    logs)
        echo "Viewing container logs (Ctrl+C to exit)..."
        echo "Showing MySQL logs:"
        podman logs -f huali-mysql
        ;;
    
    status)
        echo "Container status:"
        podman ps -a --filter name=huali --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        ;;
    
    clean)
        echo "WARNING: This will delete all containers and data!"
        read -p "Press 'y' to continue or any other key to cancel: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Cleaning containers and data..."
            podman stop huali-mysql huali-redis 2>/dev/null || true
            podman rm -v huali-mysql huali-redis 2>/dev/null || true
            echo "[OK] Containers and data cleaned"
        else
            echo "Cancelled"
            exit 0
        fi
        ;;
    
    *)
        echo "Usage: $0 {stop|restart|logs|status|clean}"
        exit 1
        ;;
esac
