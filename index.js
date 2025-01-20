// index.js
/*
script that scrapes the videos from the channels specified in channels.txt
*/
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs').promises;
const path = require('path');

// used to shuffle the channels
function shuffle(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}


puppeteer.use(StealthPlugin());

async function extractVideoDetails(page) {
  return await page.evaluate(() => {
    const videos = document.querySelectorAll("ytd-rich-grid-media");
    return Array.from(videos).map(video => {
      const titleElement = video.querySelector("#video-title-link");
      const viewString = titleElement ? titleElement.getAttribute('aria-label') : "";
      const views = viewString.match(/([0-9,]+) views/) 
        ? parseInt(viewString.match(/([0-9,]+) views/)[1].replace(/,/g, '')) 
        : 0;
      const videoUrl = titleElement ? titleElement.href : "";
      const videoId = videoUrl.split('v=')[1];
      
      return {
        title: titleElement ? titleElement.textContent.trim() : "",
        views,
        url: videoUrl,
        videoId,
        timeScraped: new Date().toISOString()
      };
    });
  });
}

async function scrapeChannel(channelId, browser) {
  const page = await browser.newPage();
  
  try {
    // go to the channel's videos tab
    await page.goto(`https://www.youtube.com/c/${channelId}/videos`, {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    // wait for the video grid to load
    await page.waitForSelector("ytd-rich-grid-media");
    
    // 2 scrolls
    for (let i = 0; i < 2; i++) {
      await page.evaluate(() => {
        window.scrollTo(0, document.body.scrollHeight);
      });
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    const videos = await extractVideoDetails(page);
    
    await fs.writeFile(
      path.join('temp', `${channelId}_videos.json`),
      JSON.stringify({
        channelId,
        videos
      }, null, 2)
    );

  } catch (error) {
    console.error(`Error scraping channel ${channelId}:`, error);
  } finally {
    await page.close();
  }
}

async function main() {
  await fs.mkdir('temp').catch(() => {});
  
  let channels = (await fs.readFile('channels.txt', 'utf-8'))
    .split('\n')
    .filter(line => line.trim());
  
  channels = shuffle(channels);
  
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox'],
    defaultViewport: null
  });

  try {
    for (const channelId of channels) {
      console.log(`Processing channel: ${channelId}`);
      await scrapeChannel(channelId.trim(), browser);
      // random sleeps 😴
      await new Promise(r => setTimeout(r, 2000 + Math.random() * 3000));
    }
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
