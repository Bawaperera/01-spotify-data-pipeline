#!/bin/bash
echo "=== Spotify Data Pipeline — Setup ==="

# Create virtual environment
python3 -m venv venv
echo " Virtual environment created"

# Activate and install
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo " Dependencies installed"

echo ""
echo "=== Setup complete! ==="
echo "Next steps:"
echo "  1. Place your Spotify CSV in data/raw/"
echo "  2. Run the pipeline:  python src/pipeline.py"
echo "  3. Launch dashboard:  streamlit run dashboard/app.py"
