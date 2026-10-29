#!/bin/bash

# Define installation directory in user's home folder
INSTALL_DIR="$HOME/.local/share/EasyCreateReports"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "=== Installing EasyCreateReports ==="

# Install system dependencies (Python, PyQt6, WebEngine, YAML, xhtml2pdf)
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pyqt6 python3-pyqt6.qtwebengine python3-yaml python3-xhtml2pdf

# Create application directory and copy files
echo "Copying files to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -r * "$INSTALL_DIR/"

# Create executable launcher script (with GPU disabling to avoid hardware/Vulkan issues)
cat << 'EOF' > "$INSTALL_DIR/run.sh"
#!/bin/bash
cd "$HOME/.local/share/EasyCreateReports"
export QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu"
python3 app_gui.py
EOF
chmod +x "$INSTALL_DIR/run.sh"

# Create Desktop Shortcut for Ubuntu application menu
echo "Creating application menu shortcut..."
mkdir -p "$DESKTOP_DIR"
cat << EOF > "$DESKTOP_DIR/easy-create-reports.desktop"
[Desktop Entry]
Name=EasyCreateReports
Comment=Municipal Report Generator
Exec=$INSTALL_DIR/run.sh
Icon=$INSTALL_DIR/icon.png
Terminal=false
Type=Application
Categories=Office;Utility;
EOF

chmod +x "$DESKTOP_DIR/easy-create-reports.desktop"
update-desktop-database "$DESKTOP_DIR" 2>/dev/null

echo "=== Installation completed successfully! ==="
echo "You can now search for 'EasyCreateReports' in your Ubuntu application menu."