//comment_scrape.js
/*
script that scrapes the comments from a youtube video
*/
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const { spawn, exec } = require('child_process');
const fs = require('fs');
const fsp = require('fs').promises;
const { executablePath } = require('puppeteer')

puppeteer.use(StealthPlugin());

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


async function run() {
    if (!fs.existsSync('transcript_scrape/comments.csv')){
        fs.writeFile('transcript_scrape/comments.csv', '', function () { console.log('') })
    }
    if (!fs.existsSync('output/com_youtubei_v1_next/data.json')){
        fs.writeFile('output/com_youtubei_v1_next/data.json', '', function () { console.log('') })
    }

    try {
        // launching browser
        const browser = await puppeteer.launch({
            headless: false,
            args: [
                '--proxy-server=http://localhost:8080',
                '--no-sandbox',
                '--ignore-certificate-errors',
                '--ignore-certificate-errors-spki-list'
            ],
            ignoreHTTPSErrors: true
        });

        const page = await browser.newPage();
        // okay browser launched...
        // url is read in here via command line
        const targetUrl = process.argv[2];
        if (!targetUrl) {
            console.error('Please provide a YouTube video URL as an argument');
            process.exit(1);
        }
        console.log(`Visiting ${targetUrl}`);
        await page.goto(targetUrl, { waitUntil: 'networkidle2' });
        const scrollDown = async (count) => {
            for (let i = 0; i < count; i++) {
                await page.evaluate(() => {
                    window.scrollBy(0, window.innerHeight);
                });
                await sleep(3000);
            }
        };
        // expand all comments "show more"
        const clickAllButtons = async () => {
            const buttons = await page.$$('button.yt-spec-button-shape-next.yt-spec-button-shape-next--text.yt-spec-button-shape-next--call-to-action.yt-spec-button-shape-next--size-m.yt-spec-button-shape-next--icon-leading.yt-spec-button-shape-next--align-by-text');
            for (const button of buttons) {
                console.log("Clicking button");
                await button.click();
                //await sleep(100);
            }
        };

        await scrollDown(15);
        await clickAllButtons();



        await scrollDown(2);
        await browser.close();

        console.log("Comment scraping completed successfully.");
        process.exit(0);
    } catch (error) {
        console.error(error);
        process.exit(1);
    }
}

run().catch((error) => {
    console.error(error);
    // we're shutting down the browser here
    // keep in mind, we've only read in one url by this point... bottleneck!!
    process.exit(1);
});
