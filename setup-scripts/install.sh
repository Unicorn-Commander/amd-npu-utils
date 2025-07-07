#!/bin/bash

# Unicorn Commander - NPU Voice Assistant Pro Installation Script
# Complete setup for desktop integration and dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_header() { echo -e "${PURPLE}$1${NC}"; }

# Project paths
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="Unicorn Commander"

log_header "🦄 Installing $PROJECT_NAME - NPU Voice Assistant Pro"
log_header "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

log_info "Project directory: $PROJECT_DIR"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    log_error "Do not run this script as root. It will prompt for sudo when needed."
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python 3
    if ! command_exists python3; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    log_success "Python 3: $(python3 --version)"
    
    # Check pip3
    if ! command_exists pip3; then
        log_warning "pip3 not found, installing..."
        sudo apt update && sudo apt install -y python3-pip
    fi
    log_success "pip3 available"
    
    # Check desktop environment
    if [[ "$XDG_CURRENT_DESKTOP" == *"KDE"* ]]; then
        log_success "KDE Desktop detected - optimal for Qt6 applications"
    elif [[ "$XDG_CURRENT_DESKTOP" ]]; then
        log_warning "Desktop: $XDG_CURRENT_DESKTOP (KDE recommended for best experience)"
    else
        log_warning "Desktop environment not detected"
    fi
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Essential packages
    PACKAGES=(
        "PySide6"
        "PyQt6" 
        "numpy"
        "scipy"
        "soundfile"
        "sounddevice"
        "librosa"
        "transformers"
        "torch"
        "onnxruntime"
        "pydub"
        "webrtcvad"
        "openwakeword"
    )
    
    for package in "${PACKAGES[@]}"; do
        log_info "Installing $package..."
        if pip3 install "$package" --user; then
            log_success "$package installed"
        else
            log_warning "Failed to install $package (may already be installed)"
        fi
    done
}

# Set up desktop integration
setup_desktop_integration() {
    log_info "Setting up desktop integration..."
    
    # Directories
    APPLICATIONS_DIR="$HOME/.local/share/applications"
    ICONS_DIR="$HOME/.local/share/icons"
    AUTOSTART_DIR="$HOME/.config/autostart"
    
    # Create directories
    mkdir -p "$APPLICATIONS_DIR"
    mkdir -p "$ICONS_DIR"
    mkdir -p "$AUTOSTART_DIR"
    
    # Copy icon
    ICON_SOURCE="$PROJECT_DIR/unicorn-aware.png"
    ICON_DEST="$ICONS_DIR/unicorn-commander.png"
    
    if [[ -f "$ICON_SOURCE" ]]; then
        cp "$ICON_SOURCE" "$ICON_DEST"
        log_success "Icon installed: $ICON_DEST"
    else
        log_warning "Icon file not found: $ICON_SOURCE"
    fi
    
    # Update desktop file with correct paths
    DESKTOP_FILE="$PROJECT_DIR/unicorn_commander.desktop"
    DESKTOP_DEST="$APPLICATIONS_DIR/unicorn_commander.desktop"
    
    # Create updated desktop file
    cat > "$DESKTOP_DEST" << EOF
[Desktop Entry]
Name=Unicorn Commander
Comment=🦄 NPU Voice Assistant Pro - Real-time Speech Processing
Exec=$PROJECT_DIR/launch_unicorn_commander.sh
Icon=$ICON_DEST
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Utility;
Keywords=voice;assistant;speech;transcription;NPU;AI;
StartupNotify=true
Path=$PROJECT_DIR
EOF

    # Make executable
    chmod +x "$DESKTOP_DEST"
    chmod +x "$PROJECT_DIR/launch_unicorn_commander.sh"
    chmod +x "$PROJECT_DIR/unicorn_tray_app.py"
    chmod +x "$PROJECT_DIR/whisperx_npu_gui_qt6.py"
    
    log_success "Desktop entry installed: $DESKTOP_DEST"
    
    # Update desktop database
    if command_exists update-desktop-database; then
        update-desktop-database "$APPLICATIONS_DIR"
        log_success "Desktop database updated"
    fi
}

# Create autostart entry (optional)
setup_autostart() {
    read -p "Would you like Unicorn Commander to start automatically at login? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        AUTOSTART_FILE="$HOME/.config/autostart/unicorn_commander.desktop"
        
        cat > "$AUTOSTART_FILE" << EOF
[Desktop Entry]
Name=Unicorn Commander Tray
Comment=🦄 NPU Voice Assistant Pro - Background Service
Exec=$PROJECT_DIR/unicorn_tray_app.py
Icon=$HOME/.local/share/icons/unicorn-commander.png
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Utility;
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Path=$PROJECT_DIR
EOF
        
        chmod +x "$AUTOSTART_FILE"
        log_success "Autostart entry created: $AUTOSTART_FILE"
    else
        log_info "Autostart not configured"
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Check files
    FILES_TO_CHECK=(
        "$PROJECT_DIR/whisperx_npu_gui_qt6.py"
        "$PROJECT_DIR/unicorn_tray_app.py"
        "$PROJECT_DIR/launch_unicorn_commander.sh"
        "$HOME/.local/share/applications/unicorn_commander.desktop"
        "$HOME/.local/share/icons/unicorn-commander.png"
    )
    
    for file in "${FILES_TO_CHECK[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "Found: $file"
        else
            log_warning "Missing: $file"
        fi
    done
    
    # Test Python imports
    log_info "Testing Python imports..."
    if python3 -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')" 2>/dev/null; then
        log_success "PySide6 import test passed"
    else
        log_warning "PySide6 import test failed"
    fi
    
    if python3 -c "import numpy, torch, transformers; print('ML libraries OK')" 2>/dev/null; then
        log_success "ML libraries import test passed"
    else
        log_warning "Some ML libraries may be missing"
    fi
}

# Create uninstall script
create_uninstall_script() {
    log_info "Creating uninstall script..."
    
    cat > "$PROJECT_DIR/uninstall.sh" << 'EOF'
#!/bin/bash

# Unicorn Commander Uninstaller

echo "🦄 Uninstalling Unicorn Commander..."

# Remove desktop files
rm -f "$HOME/.local/share/applications/unicorn_commander.desktop"
rm -f "$HOME/.config/autostart/unicorn_commander.desktop"
rm -f "$HOME/.local/share/icons/unicorn-commander.png"

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications"
fi

echo "✓ Unicorn Commander uninstalled"
echo "Note: Python packages and project files remain for manual removal"
EOF
    
    chmod +x "$PROJECT_DIR/uninstall.sh"
    log_success "Uninstall script created: $PROJECT_DIR/uninstall.sh"
}

# Main installation flow
main() {
    check_requirements
    echo
    
    install_dependencies
    echo
    
    setup_desktop_integration
    echo
    
    setup_autostart
    echo
    
    verify_installation
    echo
    
    create_uninstall_script
    echo
    
    log_header "🦄 Installation Complete!"
    log_header "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    log_success "Unicorn Commander has been installed successfully!"
    echo
    log_info "You can now:"
    log_info "  • Find 'Unicorn Commander' in your application launcher"
    log_info "  • Run the tray app: ./unicorn_tray_app.py"
    log_info "  • Launch the GUI directly: ./whisperx_npu_gui_qt6.py"
    log_info "  • Use the launcher script: ./launch_unicorn_commander.sh"
    echo
    log_info "To uninstall: run ./uninstall.sh"
    echo
    
    # Offer to launch
    read -p "Would you like to launch Unicorn Commander now? (Y/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        log_info "Launching Unicorn Commander..."
        "$PROJECT_DIR/launch_unicorn_commander.sh" &
        log_success "Unicorn Commander launched!"
    fi
}

# Run main installation
main "$@"