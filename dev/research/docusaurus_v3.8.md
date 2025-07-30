# Docusaurus 3.8
May 26, 2025 · 11 min read
[![Sébastien Lorber](https://github.com/slorber.png)](https://docusaurus.io/blog/authors/slorber)
[Sébastien Lorber](https://docusaurus.io/blog/authors/slorber)
Docusaurus maintainer, This Week In React editor
[](https://bsky.app/profile/sebastienlorber.com "Bluesky")[](https://x.com/sebastienlorber "X")[](https://www.linkedin.com/in/sebastienlorber/ "LinkedIn")[](https://github.com/slorber "GitHub")[](https://www.instagram.com/thisweekinreact "Instagram")[](https://thisweekinreact.com "newsletter")
We are happy to announce **Docusaurus 3.8**.
This release improves build performance, includes new features and introduces "Future Flags" to prepare your site for Docusaurus 4.
Upgrading is easy. We follow [Semantic Versioning](https://semver.org/), and minor version updates have **no breaking changes** , accordingly to our [release process](https://docusaurus.io/community/release-process).
![Docusaurus blog post social card](https://docusaurus.io/assets/images/social-card-b49b847d6c81d30ed3b8fff82aed14b5.png)
## Performance[​](https://docusaurus.io/blog/releases/3.8#performance "Direct link to Performance")
This release keeps improving our build infrastructure performance with various optimizations, and 2 new Docusaurus Faster options.
### Docusaurus Faster[​](https://docusaurus.io/blog/releases/3.8#docusaurus-faster "Direct link to Docusaurus Faster")
[Docusaurus Faster](https://github.com/facebook/docusaurus/issues/10556) has been introduced in [Docusaurus v3.6](https://docusaurus.io/blog/releases/3.6#docusaurus-faster), and permits you to opt-in for our upgraded build infrastructure and helps you build your site much faster. The experimental flags can be turned on individually, but we recommend to turn them all at once with this convenient shortcut:
```
const config ={  
future:{  
experimental_faster:true,  
},  
};  

```

Don't forget to install the `@docusaurus/faster` dependency first!
#### Persistent Cache[​](https://docusaurus.io/blog/releases/3.8#persistent-cache "Direct link to Persistent Cache")
In [#10931](https://github.com/facebook/docusaurus/pull/10931), we have enabled the **[Rspack persistent cache](https://rspack.dev/blog/announcing-1-2#persistent-cache)**. Similarly to the [Webpack persistent cache](https://webpack.js.org/blog/2020-10-10-webpack-5-release/#persistent-caching) (already supported), it permits to greatly speed up the bundling of the Docusaurus app on subsequent builds.
In practice, your site should build much faster if you run `docusaurus build` a second time.
This feature depends on using the [Rspack bundler](https://rspack.dev/), and can be turned on with the `rspackPersistentCache` flag:
```
const config ={  
future:{  
experimental_faster:{  
rspackBundler:true,// required flag  
rspackPersistentCache:true,// new flag  
},  
},  
};  

```

The persistent cache requires preserving the `./node_modules/.cache` folder across builds.
Popular CDNs such as Netlify and Vercel do that for you automatically. Depending on your CI and deployment pipeline, additional configuration can be needed to preserve the cache.
**Result** : On average, you can expect your site's bundling time to be ~2-5× faster on rebuilds 🔥. The impact can be even more significant if you [disable the optional `concatenateModule` optimization](https://github.com/facebook/docusaurus/discussions/11199).
#### Worker Threads[​](https://docusaurus.io/blog/releases/3.8#worker-threads "Direct link to Worker Threads")
In [#10826](https://github.com/facebook/docusaurus/pull/10826), we introduced a [Node.js Worker Thread pool](https://github.com/tinylibs/tinypool) to run the static side generation code. With this new strategy, we can better leverage all the available CPUs, reduce static site generation time, and contain potential memory leaks.
This feature can be turned on with the `ssgWorkerThreads` flag, and requires the [`v4.removeLegacyPostBuildHeadAttribute`](https://docusaurus.io/blog/releases/3.8#postbuild-change) Future Flag to be turned on:
```
const config ={  
future:{  
v4:{  
removeLegacyPostBuildHeadAttribute:true,// required  
},  
experimental_faster:{  
ssgWorkerThreads:true,  
},  
},  
};  

```

**Result** : On average, you can expect your site's static site generation time to be ~2× times faster 🔥. This was measured on a MacBook Pro M3 and result may vary depending on your CI.
### Other Optimizations[​](https://docusaurus.io/blog/releases/3.8#other-optimizations "Direct link to Other Optimizations")
We identified and resolved several major bottlenecks, including:
  * In [#11007](https://github.com/facebook/docusaurus/pull/11007), we optimized the dev server startup time for macOS users. We figured out that the code to open your browser used expensive synchronous/blocking calls that prevented the bundler from doing its work. From now on, the bundler and the macOS browser opening will run in parallel, leading to a faster `docusaurus start` experience for all macOS users.
  * In [#11163](https://github.com/facebook/docusaurus/pull/11163), we noticed that the docs `showLastUpdateAuthor` and `showLastUpdateTime` are quite expensive, and require to run a `git log` command for each document. On large sites, running these commands in parallel can exhaust the system and lead to Node.js `EBADF` errors. We implemented a Git command queue to avoid exhausting the system, which also slightly increased performance of our plugin's `loadContent()` lifecycle.
  * In [#10885](https://github.com/facebook/docusaurus/pull/10885), we implemented an SVG sprite for the external link icon. Due to its repeated appearance in various places of your site (navbar, footer, sidebars...), using a React SVG component lead to duplicated SVG markup in the final HTML. Using a sprite permits to only embed the icon SVG once, reducing the generated HTML size and the static generation time. We [plan to use more SVG sprites](https://github.com/facebook/docusaurus/issues/5865) in the future.
  * In [#11176](https://github.com/facebook/docusaurus/pull/11176), we fine-tuned the webpack/Rspack configuration to remove useless optimizations.


If bundling time is a concern, consider disabling the optional `concatenateModule` bundler optimization. We explain the tradeoffs and how to do it [here](https://github.com/facebook/docusaurus/discussions/11199). It only saves 3% JS, and for a very large site, this change was incredibly impactful: 4x faster on cold builds, x16 faster rebuilds 🔥.
### Impact[​](https://docusaurus.io/blog/releases/3.8#impact "Direct link to Impact")
We have upgraded the [React Native website to Docusaurus v3.8](https://github.com/facebook/react-native-website/pull/4607) already. Here's an updated benchmark showing the global Docusaurus Faster impact on total build time for a site with ~2000 pages:
ReactNative.dev | Cold Build | Warm Rebuild  
---|---|---  
🐢 Docusaurus Slower | 120s (baseline) | 33s (3.6 × faster)  
⚡️ Docusaurus Faster | 31s (3.8 × faster) | 17s (7 × faster)  
We measured similar results on our website:
Docusaurus.io | Cold Build | Warm Rebuild  
---|---|---  
🐢️ Docusaurus Slower | 146s (baseline) | 45s (3.2 × faster)  
⚡️ Docusaurus Faster | 42s (3.5 × faster) | 24s (6.1 × faster)  
You can also expect memory usage improvements, and a faster `docusaurus start` experience.
## Future Flags[​](https://docusaurus.io/blog/releases/3.8#future-flags "Direct link to Future Flags")
The Docusaurus v4 Future Flags let you **opt-in for upcoming Docusaurus v4 breaking changes** , and help you manage them incrementally, one at a time. Enabling all the future flags will make your site easier to upgrade to Docusaurus v4 when it's released.
The concept of Future Flags is not our invention. It has been popularized in the Remix community. You can read more about this gradual feature adoption strategy here:
  * [Gradual Feature Adoption with Future Flags](https://remix.run/docs/en/main/guides/api-development-strategy)
  * [Future Proofing Your Remix App](https://remix.run/blog/future-flags)


You can turn all the v4 Future Flags on at once with the following shortcut:
```
const config ={  
future:{  
v4:true,  
},  
};  

```

This way, you are sure to always keep your site prepared for Docusaurus v4. Be aware that we'll introduce more Future Flags in the next minor versions. When upgrading, always read our release blog posts to understand the new breaking changes you opt into.
### CSS Cascade Layers[​](https://docusaurus.io/blog/releases/3.8#css-cascade-layers "Direct link to CSS Cascade Layers")
In Docusaurus v4, we plan to leverage [CSS Cascade Layers](https://css-tricks.com/css-cascade-layers/). This modern CSS feature is widely supported and permits to group CSS rules in layers of specificity. It is particularly useful to give you more control over the CSS cascade. It makes the CSS rules less dependent on their insertion order. Your un-layered rules will now always override the layered CSS we provide.
In [#11142](https://github.com/facebook/docusaurus/pull/11142), we implemented a new experimental [`@docusaurus/plugin-css-cascade-layers`](https://docusaurus.io/docs/api/plugins/@docusaurus/plugin-css-cascade-layers) that you can turn on through the `v4.useCssCascadeLayers` flag if you use the classic preset:
```
exportdefault{  
future:{  
v4:{  
useCssCascadeLayers:true,  
},  
},  
};  

```

We consider this feature as a **breaking change** because it can slightly alter the CSS rules application order in customized sites. These issues are usually limited, and relatively easy to fix (see for example the [React Native CSS changes](https://github.com/facebook/react-native-website/pull/4607)). Sites that do not provide custom CSS and do not swizzle any component should not be affected.
In practice, it permits to automatically apply built-in CSS Cascade Layers to all the CSS we provide, including our opinionated CSS framework [Infima](https://infima.dev/):
```
@layer docusaurus.infima{  
h1{  
/* Infima css rules */  
}  
pre{  
/* Infima css rules */  
}  
}  

```

Layers can help solves our long-standing [Global CSS pollution issue](https://github.com/facebook/docusaurus/issues/6032). Our built-in global CSS rules may conflict with yours, making it harder to use Docusaurus to create playgrounds, demos and embedded widgets that are isolated from our CSS. Thankfully, [CSS Cascade Layers can be reverted](https://mayank.co/blog/revert-layer/) to create HTML subtrees that are not affected by the CSS Docusaurus provides.
Reverting layers
As [this issue](https://github.com/facebook/docusaurus/pull/11142) and [this blog post](https://mayank.co/blog/revert-layer/) explain, it is possible to revert layers to isolate an HTML subtree from the CSS that comes from that layer.
In practice, you can create a `.my-playground` class to revert the global CSS coming from Infima:
```
/* The "impossible" :not() selector helps increase the specificity */  
.my-playground:not(#a#b){  
&,  
  *{  
@layer docusaurus.infima{  
all: revert-layer;  
}  
}  
}  

```

Then you can apply this class to any HTML element, so that Infima doesn't apply to any of its children. The HTML subtree becomes isolated from our built-in CSS.
/tests/pages/style-isolation?docusaurus-data-navbar=false
###  `postBuild()` Change[​](https://docusaurus.io/blog/releases/3.8#postbuild-change "Direct link to postbuild-change")
In [#10850](https://github.com/facebook/docusaurus/pull/10850), we added a new `removeLegacyPostBuildHeadAttribute` Future Flag that slightly changes the signature of the `postBuild()` plugin lifecycle method, removing the `head` attribute.
```
exportdefault{  
future:{  
v4:{  
removeLegacyPostBuildHeadAttribute:true,  
},  
},  
};  

```

This legacy data structure is coming from our [react-helmet-async](https://github.com/staylor/react-helmet-async) dependency and should have never been exposed as public API in the first place. It is not serializable, which prevents us from implementing [Worker Threads for the static site generation](https://docusaurus.io/blog/releases/3.8#worker-threads).
While technically a **breaking change** , we believe this change will not affect anyone. We couldn't find any open source plugin that uses the `head` parameter that this method receives. If turning this flag on breaks your site, please let us know [here](https://github.com/facebook/docusaurus/pull/10850).
## System Color Mode[​](https://docusaurus.io/blog/releases/3.8#system-color-mode "Direct link to System Color Mode")
In [#10987](https://github.com/facebook/docusaurus/pull/10987), the classic theme now lets you revert the color mode to the system/OS value.
http://localhost:3000
## Code Block Refactor[​](https://docusaurus.io/blog/releases/3.8#code-block-refactor "Direct link to Code Block Refactor")
In [#11058](https://github.com/facebook/docusaurus/pull/11058), [#11059](https://github.com/facebook/docusaurus/pull/11059), [#11062](https://github.com/facebook/docusaurus/pull/11062) and [#11077](https://github.com/facebook/docusaurus/pull/11077), the theme code block components have been significantly refactored in a way that should be much easier to swizzle and extend.
According to our [release process](https://docusaurus.io/community/release-process), this is not a breaking change, but sites that have swizzled these components may need to upgrade them.
## Translations[​](https://docusaurus.io/blog/releases/3.8#translations "Direct link to Translations")
  * 🇹🇷 [#10893](https://github.com/facebook/docusaurus/pull/10893): Add missing Turkish theme translations.
  * 🇵🇱 [#10884](https://github.com/facebook/docusaurus/pull/10884): Add missing Polish theme translations.
  * 🇨🇳 [#10816](https://github.com/facebook/docusaurus/pull/10816): Add missing Chinese theme translations.
  * 🇯🇵 [#11030](https://github.com/facebook/docusaurus/pull/11030): Add missing Japanese theme translations.


## Maintenance[​](https://docusaurus.io/blog/releases/3.8#maintenance "Direct link to Maintenance")
Docusaurus 3.8 is ready for [Node.js 24](https://github.com/facebook/docusaurus/pull/11168) and [TypeScript 5.8](https://github.com/facebook/docusaurus/pull/10966).
We also removed useless npm packages and internalizing unmaintained ones:
  * In [#11010](https://github.com/facebook/docusaurus/pull/11010) and [#11014](https://github.com/facebook/docusaurus/pull/11014), we internalized the unmaintained `react-ideal-image` and `react-waypoint` package used in `@docusaurus/plugin-ideal-image`, and made them compatible with React 19.
  * In [#10956](https://github.com/facebook/docusaurus/pull/10956), we removed our dependency to the unmaintained `react-dev-utils` package (from Create-React-App).
  * In [#10358](https://github.com/facebook/docusaurus/pull/10358), we replaced the unmaintained `shelljs` package by `execa`
  * In [#11138](https://github.com/facebook/docusaurus/pull/11138), we removed the `reading-time` package in favor of the built-in `Intl.Segmenter` standard API to compute blog post reading times.
  * In [#11037](https://github.com/facebook/docusaurus/pull/11037), we removed the useless `clean-webpack-plugin`.


## Other changes[​](https://docusaurus.io/blog/releases/3.8#other-changes "Direct link to Other changes")
Other notable changes include:
  * In [#10852](https://github.com/facebook/docusaurus/pull/10852), the theme `docsVersionDropdown` navbar item now accepts a `versions` attribute.
  * In [#10953](https://github.com/facebook/docusaurus/pull/10953), the `@docusaurus/remark-plugin-npm2yarn` plugin now supports Bun tabs conversions by default.
  * In [#10945](https://github.com/facebook/docusaurus/pull/10945), more stable CSS classes are now applied to the main theme layout elements, to let you create more reliable CSS selectors.
  * In [#10846](https://github.com/facebook/docusaurus/pull/10846), the Markdown code block `showLineNumbers` metastring can now accept a number to initialize the line counter initial value.
  * In [#11090](https://github.com/facebook/docusaurus/pull/11090), we made it easier to provide a custom page title formatter.
  * In [#11088](https://github.com/facebook/docusaurus/pull/11088), the page plugin now supports `frontMatter.slug` like docs and blog plugins already do.
  * In [#10875](https://github.com/facebook/docusaurus/pull/10875), the docs versioning CLI now also copies localized docs JSON translation files.


Check the **[3.8.0 changelog entry](https://docusaurus.io/changelog/3.8.0)** for an exhaustive list of changes.
**Tags:**
  * [Release](https://docusaurus.io/blog/tags/release "Blog posts about Docusaurus' new releases")
