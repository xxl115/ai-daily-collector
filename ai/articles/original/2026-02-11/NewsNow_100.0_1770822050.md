---
title: "GLM5 Released on Z.ai Platform"
url: "https://news.ycombinator.com/item?id=46974853"
source: "NewsNow 中文热点"
date: 2026-02-11
score: 100.0
---

# GLM5 Released on Z.ai Platform

**来源**: [NewsNow 中文热点](https://news.ycombinator.com/item?id=46974853) | **热度**: 100.0

## 原文内容

Title: GLM5 Released on Z.ai Platform

URL Source: http://news.ycombinator.com/item?id=46974853

Markdown Content:
![Image 1](https://news.ycombinator.com/s.gif)[](https://news.ycombinator.com/vote?id=46975155&how=up&goto=item%3Fid%3D46974853)It's looking like we'll have Chinese OSS to thank for being able to host our own intelligence, free from the whims of proprietary megacorps. I know it doesn't make financial sense to self-host given how cheap OSS inference APIs are now, but it's comforting not being beholden to anyone or requiring a persistent internet connection for on-premise intelligence. Didn't expect to go back to macOS but their basically the only feasible consumer option for running large models locally.
![Image 2](https://news.ycombinator.com/s.gif)[](https://news.ycombinator.com/vote?id=46975594&how=up&goto=item%3Fid%3D46974853)> doesn't make financial sense to self-host I guess that's debatable. I regularly run out of quota on my claude max subscription. When that happens, I can sort of kind of get by with my modest setup (2x RTX3090) and quantized Qwen3. And this does not even account for privacy and availability. I'm in Canada, and as the US is slowly consumed by its spiral of self-destruction, I fully expect at some point a digital iron curtain will go up. I think it's prudent to have alternatives, especially with these paradigm-shattering tools.

![Image 3](https://news.ycombinator.com/s.gif)[](https://news.ycombinator.com/vote?id=46975746&how=up&goto=item%3Fid%3D46974853)our laptops, devices, phones, equipments, home stuff are all powered by Chinese companies. It wouldn't surprise me if at some point in the future my local "Alexa" assistant will be fully powered by local Chinese OSS models with Chinese GPUs and RAM.
![Image 4](https://news.ycombinator.com/s.gif)[](https://news.ycombinator.com/vote?id=46975705&how=up&goto=item%3Fid%3D46974853)> Didn't expect to go back to macOS but their basically the only feasible consumer option for running large models locally. Framework Desktop! Half the memory bandwidth of M4 Max, but much cheaper.
![Image 5](https://news.ycombinator.com/s.gif)[](https://news.ycombinator.com/vote?id=46975340&how=up&goto=item%3Fid%3D46974853)> Didn't expect to go back to macOS but their basically the only feasible consumer option for running large models locally. I presume here you are referring to running on the device in your lap. How about a headless linux inference box in the closet / basement? Return of the home network!
![Image 6](https://news.ycombinator.com/s.gif)[](https://news.ycombinator.com/vote?id=46975711&how=up&goto=item%3Fid%3D46974853)Not feasible for Large models, it takes 2x M3 512GB Ultra's to run the full Kimi K2.5 model at a respectable 24 tok/s. Hopefully the M5 Ultra will can improve on that.
![Image 7](https://news.ycombinator.com/s.gif)[](https://news.ycombinator.com/vote?id=46975409&how=up&goto=item%3Fid%3D46974853)Apple devices have high memory bandwidth necessary to run LLMs at reasonable rates. It’s possible to build a Linux box that does the same but you’ll be spending a lot more to get there. With Apple, a $500 Mac Mini has memory bandwidth that you just can’t get anywhere else for the price.
![Image 8](https://news.ycombinator.com/s.gif)[](https://news.ycombinator.com/vote?id=46975745&how=up&goto=item%3Fid%3D46974853)With Apple devices you get very fast predictions once it gets going but it is inferior to nvidia precisely during prefetch (processing prompt/context) before it really gets going. For our code assistant use cases the local inference on Macs will tend to favor workflows where there is a lot of generation and little reading and this is the opposite of how many of use use Claude Code. Source: I started getting Mac Studios with max ram as soon as the first llama model was released.
![Image 9](https://news.ycombinator.com/s.gif)[](https://news.ycombinator.com/vote?id=46975491&how=up&goto=item%3Fid%3D46974853)And then only Apple devices have 512GB of unified memory, which matters when you have to combine larger models (even MoE) with the bigger context/KV caching you need for agentic workflows. You can make do with less, but only by slowing things down a whole lot.
![Image 10](https://news.ycombinator.com/s.gif)[](https://news.ycombinator.com/vote?id=46975456&how=up&goto=item%3Fid%3D46974853)But a $500 Mac Mini has nowhere near the memory _capacity_ to run such a model. You'd need at least 2 512GB machines chained together to run this model. Maybe 1 if you quantized the crap out of it. And Apple completely overcharges for memory, so. This is a model you use via a cheap API provider like DeepInfra, or get on their coding plan. It's nice that it will be available as open weights, but not practical for mere mortals to run. But I _can_ see a large corporation that wants to avoid sending code offsite setting up their own private infra to host it.
![Image 11](https://news.ycombinator.com/s.gif)[](https://news.ycombinator.com/vote?id=4

---
*自动采集于 2026-02-11 23:00:54 (北京时间)*
