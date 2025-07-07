#!/bin/bash

# WhisperX NPU Project Setup Script
# This script helps set up the project on a fresh system

set -e  # Exit on any error

echo "🚀 Setting up WhisperX NPU Project..."

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the whisper_npu_project directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required system dependencies
echo "🔍 Checking system dependencies..."

if ! command_exists python3; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

if ! command_exists pip3; then
    echo "❌ pip3 is required but not installed"
    exit 1
fi

if ! command_exists git; then
    echo "❌ git is required but not installed"
    exit 1
fi

echo "✅ System dependencies check passed"

# Create virtual environment
echo "📦 Creating Python virtual environment..."
if [ ! -d "whisperx_env" ]; then
    python3 -m venv whisperx_env
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source whisperx_env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Clone required repositories if they don't exist
echo "📂 Checking for required repositories..."

if [ ! -d "mlir-aie" ]; then
    echo "📥 Cloning mlir-aie repository..."
    git clone https://github.com/Xilinx/mlir-aie.git
    echo "✅ mlir-aie cloned"
else
    echo "ℹ️  mlir-aie directory already exists"
fi

if [ ! -d "xdna-driver" ]; then
    echo "📥 Cloning xdna-driver repository..."
    git clone https://github.com/amd/xdna-driver.git
    echo "✅ xdna-driver cloned"
else
    echo "ℹ️  xdna-driver directory already exists"
fi

# Create activation script
echo "📝 Creating activation script..."
cat > activate_whisperx.sh << 'EOF'
#!/bin/bash
echo "🎤 Activating WhisperX NPU environment..."
source whisperx_env/bin/activate
echo "✅ Environment activated!"
echo "💡 Try: python whisperx_npu_gui.py"
EOF

chmod +x activate_whisperx.sh

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Review SETUP.md for detailed configuration instructions"
echo "   2. Source the activation script: source activate_whisperx.sh"
echo "   3. Check USAGE.md for how to use the application"
echo ""
echo "🔧 For NPU-specific setup, please see SETUP.md for:"
echo "   - NPU driver installation"
echo "   - XRT runtime setup"
echo "   - MLIR-AIE environment configuration"
echo ""
echo "🚀 Ready to start! Run: source activate_whisperx.sh"