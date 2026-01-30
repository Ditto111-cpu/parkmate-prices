# Parkmate Prices

Automated scraper for Brisbane parking prices (Wilson Parking & Secure Parking).

## How It Works

1. GitHub Actions runs weekly (Monday 6am AEST)
2. Python script scrapes pricing from Wilson and Secure Parking websites
3. Results saved to `data/prices.json`
4. Parkmate iOS app fetches this JSON for up-to-date prices

## Usage

### Fetch Latest Prices

The Parkmate app fetches prices from:
```
https://raw.githubusercontent.com/YOUR_USERNAME/parkmate-prices/main/data/prices.json
```

### Manual Trigger

Go to Actions tab → "Scrape Parking Prices" → "Run workflow"

## Disclaimer

Prices are scraped for personal, non-commercial use only. Always verify current rates on official websites before parking.

- [Wilson Parking](https://www.wilsonparking.com.au/)
- [Secure Parking](https://www.secureparking.com.au/)

## License

MIT - Personal use only.
