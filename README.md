# Keilamenu - Daily Lunch Menu Aggregator

![Keilamenu Interface](https://github.com/user-attachments/assets/d68aa0fb-5919-4170-9a01-b96e7b0b2c89)

Keilamenu is a Flask web application that aggregates and displays daily lunch menus from three downstairs restaurants: **FG by ISS**, **FoodHub by Sodexo**, and **Keila Cafe by Compass Group**. The application scrapes menu data from various sources and presents them in a clean, modern interface with search functionality and dietary preference indicators.

## Features

- 🍽️ **Daily Menu Aggregation**: Scrapes menus from three restaurant providers
- 🔍 **Search Functionality**: Search across all menus for specific dishes
- 🏷️ **Dietary Labels**: Clear indicators for vegetarian, vegan, gluten-free options
- 👨‍🍳 **Chef's Picks**: Highlighted special dishes of the day
- ❤️ **Favorites**: Add items to favorites (local storage)
- 📱 **Responsive Design**: Works on desktop and mobile devices
- ♿ **Accessibility**: Screen reader friendly with proper ARIA labels
- 🎨 **Daily Themes**: Dynamic themes that change based on the day of the week

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/Jinssi/Keilamenu.git
   cd Keilamenu
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-minimal.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your browser and go to `http://localhost:5000`

## Deployment Options

### 🐳 Docker Deployment

#### Option 1: Development Build (full dependencies)
```bash
# Build with all dependencies
docker build -t keilamenu .

# Run the container
docker run -p 5000:5000 keilamenu
```

#### Option 2: Production Build (minimal dependencies)
```bash
# Build with minimal dependencies for production
docker build -f Dockerfile.minimal -t keilamenu-minimal .

# Run the container with Gunicorn
docker run -p 5000:5000 keilamenu-minimal
```

#### Using Docker Compose
```bash
docker-compose up
```

### ☁️ Azure Cloud Deployment

For production deployment on Azure with Application Gateway, load balancing, and proper scaling, see our comprehensive [Azure Deployment Guide](DEPLOYMENT.md).

**Quick Azure deployment:**
```bash
# Deploy infrastructure
./deploy-infrastructure.sh

# Deploy application
./deploy-app.sh
```

### 🚀 Production Deployment

For production environments, use a WSGI server like Gunicorn:

```bash
# Install production dependencies
pip install -r requirements-minimal.txt

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Configuration

### Environment Variables

- `PORT`: Application port (default: 5000)
- `FLASK_ENV`: Flask environment (`development` or `production`)

### Restaurant Data Sources

The application scrapes data from:
- **ISS**: Menu API for FG restaurant
- **Sodexo**: Menu API for FoodHub
- **Compass Group**: RSS feed for Keila Cafe

When live data is unavailable, the application falls back to sample menu data to ensure the interface remains functional for demonstration purposes.

## API Endpoints

- `GET /`: Main application interface displaying all restaurant menus

## Project Structure

```
Keilamenu/
├── app.py                      # Main Flask application
├── requirements.txt            # Full development dependencies
├── requirements-minimal.txt    # Production dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose configuration
├── startup.sh                  # App Service startup script
├── deploy.sh                   # Combined deployment script
├── deploy-infrastructure.sh    # Azure infrastructure deployment
├── deploy-app.sh              # Azure application deployment
├── validate-deployment.sh      # Deployment validation script
├── DEPLOYMENT.md              # Detailed Azure deployment guide
├── infrastructure/            # Azure Bicep templates
│   ├── main.bicep            # Main infrastructure template
│   └── main.parameters.json  # Template parameters
├── static/                    # Static web assets
│   ├── styles.css            # Application styles
│   ├── isslogo.png           # ISS company logo
│   ├── sodexologo.png        # Sodexo company logo
│   └── compassgrouplogo.png  # Compass Group logo
└── templates/                 # Flask templates
    └── index.html            # Main application template
```

## How It Works

1. **Data Scraping**: The application uses web scraping to fetch menu data from three different restaurant providers
2. **Data Processing**: Each restaurant's data is processed according to its specific format and structure
3. **Fallback Data**: When scraping fails, sample data ensures the application remains functional
4. **Daily Updates**: Menus are fetched in real-time for the current day
5. **Responsive UI**: The interface adapts to different screen sizes and provides accessibility features

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Development

### Local Development Setup

```bash
# Clone and setup
git clone https://github.com/Jinssi/Keilamenu.git
cd Keilamenu

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install all dependencies (including development tools)
pip install -r requirements.txt

# Run in development mode
export FLASK_ENV=development
python app.py
```

### Making Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the changes locally
5. Submit a pull request

## Troubleshooting

### Common Issues

**Menu data not loading:**
- Check internet connectivity
- Verify restaurant websites are accessible
- Application will show sample data if scraping fails

**Application won't start:**
- Ensure Python 3.9+ is installed
- Check that all dependencies are installed: `pip install -r requirements-minimal.txt`
- Verify port 5000 is available

**Docker build fails:**
- Ensure Docker is running
- Check internet connectivity for package downloads
- Try building with `--no-cache` flag

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Support

If you encounter any issues or have questions:
1. Check this README for common solutions
2. Review the [Azure Deployment Guide](DEPLOYMENT.md) for cloud deployment issues
3. Open an issue on GitHub with detailed information about your problem
