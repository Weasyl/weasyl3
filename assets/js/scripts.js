var WZL = (function (window, document) {

    'use strict';

    ////////////////////////
    //  helper functions  //
    ////////////////////////

    // parent traversal helpers
    function getParents(el) {
        var result = [];
        while (el !== document.documentElement) {
            result.push(el);
            el = el.parentNode;
        }
        return result;
    }
    function getParentsByTagName(el, tag) {
        tag = tag.toLowerCase();
        return getParents(el).filter(function (candidate) {
            return candidate.tagName.toLowerCase() === tag;
        });
    }
    function getParentsByClassName(el, cl) {
        return getParents(el).filter(function (candidate) {
            return candidate.classList.contains(cl);
        });
    }

    // get a timestamp
    function now() {
        'use strict';
        return Date.now || new Date().getTime();
    }

    // throttle and debounce from underscore.js
    function throttle(func, wait, options) {
        'use strict';
        var context, args, result,
            timeout = null,
            previous = 0;
        if (!options) {
            options = {};
        }
        var later = function () {
            previous = options.leading === false ? 0 : now();
            timeout = null;
            result = func.apply(context, args);
            if (!timeout) {
                context = args = null;
            }
        };
        return function () {
            var now = now();
            if (!previous && options.leading === false) {
                previous = now;
            }
            var remaining = wait - (now - previous);
            context = this;
            args = arguments;
            if (remaining <= 0 || remaining > wait) {
                clearTimeout(timeout);
                timeout = null;
                previous = now;
                result = func.apply(context, args);
                if (!timeout) {
                    context = args = null;
                }
            } else if (!timeout && options.trailing !== false) {
                timeout = setTimeout(later, remaining);
            }
            return result;
        };
    }
    function debounce(func, wait, immediate) {
        'use strict';
        var timeout, args, context, timestamp, result;
        var later = function () {
            var last = now() - timestamp;
            if (last < wait && last > 0) {
                timeout = setTimeout(later, wait - last);
            } else {
                timeout = null;
                if (!immediate) {
                    result = func.apply(context, args);
                    if (!timeout) {
                        context = args = null;
                    }
                }
            }
        };
        return function () {
            context = this;
            args = arguments;
            timestamp = now();
            var callNow = immediate && !timeout;
            if (!timeout) {
                timeout = setTimeout(later, wait);
            }
            if (callNow) {
                result = func.apply(context, args);
                context = args = null;
            }
            return result;
        };
    };



    ///////////////////////
    //  generic toggles  //
    ///////////////////////

    // usage:
    // <el class="toggle" data-toggle-target="[next|parentnext|css-selector]" />
    // <el class="toggle-target" />

    var toggles = (function () {
        // use this module on .toggle elements by default
        var initEls = document.getElementsByClassName('toggle'),
            toggleList = [];

        // individual toggle object; stores element and targets
        function Toggle(el) {
            var that = this;
            this.origin = el;
            this.targets = findTargets(el);
            el.addEventListener('click', function (ev) {
                ev.preventDefault();
                that.activate();
            });
        }

        // parses a target string and returns a matching array
        function findTargets(el) {
            var targetString = el.getAttribute('data-toggle-target');
            if (!targetString) {
                return [];
            }
            if (targetString === 'next') {
                return [el.nextElementSibling];
            }
            if (targetString === 'parentnext') {
                return [el.parentNode.nextElementSibling];
            }
            if (targetString === 'parentparentnext') {
                return [el.parentNode.parentNode.nextElementSibling];
            }
            return Array.prototype.slice.call(document.querySelectorAll(targetString), 0);
        }

        // make toggle go
        Toggle.prototype.activate = function () {
            [this.origin].concat(this.targets).forEach(function (el) {
                el.classList.toggle('active');
            });
        };

        // public: make node or nodeList toggleable
        function add(els) {
            Array.prototype.slice.call(els, 0).forEach(function (el) {
                toggleList.push(new Toggle(el));
            });
        }

        // public: returns an array of all toggles on the page
        function list() {
            return toggleList;
        }

        // public: initialize by adding default elements
        function init() {
            add(initEls);
        }

        return {
            add: add,
            list: list,
            init: init
        };
    }());


    /////////////////////////////
    //  simple tabs/slideshow  //
    /////////////////////////////

    // usage:
    // <div class="tabs [automated]?">
    //      <el class="tab" />
    //      <el class="tab" />
    //      <el class="pane" />
    //      <el class="pane" />
    // </div>

    var tabs = (function () {
        var initEls = document.getElementsByClassName('tabs'),
            // TODO: consider exposing defaults
            defaults = {
                automated: false,
                automationClass: 'automated',
                tabSelector: '.tab',
                paneSelector: '.pane',
                slideDuration: 4000
            },
            tabsList = [];

        function TabGroup(container, options) {
            var that = this;

            this.container = container;
            this.automated = options.automated;
            this.tabs = Array.prototype.slice.call(container.querySelectorAll(options.tabSelector), 0);
            this.panes = Array.prototype.slice.call(container.querySelectorAll(options.paneSelector), 0);
            this.slideDuration = options.slideDuration;

            this.active = 0;
            this.count = Math.max(this.tabs.length, this.panes.length);

            this.changeTo(0);

            this.tabs.forEach(function (tab, index) {
                tab.addEventListener('click', function (ev) {
                    ev.preventDefault();
                    if (that.automated) {
                        that.pause();
                    }
                    that.changeTo(index);
                    if (that.automated) {
                        that.play();
                    }
                });
            });

            if (this.automated) {
                this.play();
            }
        }

        // switch current tabgroup to specified index
        TabGroup.prototype.changeTo = function (index) {
            this.tabs.concat(this.panes).forEach(function (el) {
                el.classList.remove('active');
                el.classList.remove('next');
                el.classList.remove('prev');
            });

            if (index === 'next') {
                index = this.nextIndex();
            }
            if (index === 'prev') {
                index = this.prevIndex();
            }

            this.active = index;

            if (this.tabs[index]) { this.tabs[index].classList.add('active'); }
            if (this.panes[index]) { this.panes[index].classList.add('active'); }
            if (this.tabs[this.nextIndex()]) { this.tabs[this.nextIndex()].classList.add('next'); }
            if (this.panes[this.nextIndex()]) { this.panes[this.nextIndex()].classList.add('next'); }
            if (this.tabs[this.prevIndex()]) { this.tabs[this.prevIndex()].classList.add('prev'); }
            if (this.panes[this.prevIndex()]) { this.panes[this.prevIndex()].classList.add('prev'); }
        };

        // returns index of the next tab; wraps around to 0
        TabGroup.prototype.nextIndex = function () {
            return (this.active + 1) % this.count;
        };

        // returns index of the previous tab; wraps around from 0
        TabGroup.prototype.prevIndex = function () {
            return this.active <= 0 ? this.count - 1 : this.active - 1;
        };

        // start automated slideshow
        TabGroup.prototype.play = function () {
            var that = this;
            that.container.classList.add('playing');
            that.timer = setInterval(function () {
                that.changeTo('next');
            }, that.slideDuration);
        };

        // pause automated slideshow
        TabGroup.prototype.pause = function () {
            var that = this;
            that.container.classList.remove('playing');
            clearInterval(that.timer);
        };

        // public: add tab functionality to element
        function add(container, options) {
            options.automated = options.automated || defaults.automated;
            options.tabSelector = options.tabSelector || defaults.tabSelector;
            options.paneSelector = options.paneSelector || defaults.paneSelector;
            options.slideDuration = options.slideDuration || defaults.slideDuration;
            tabsList.push(new TabGroup(container, options));
        }

        // public: returns array of all tab groups on the page
        function list() {
            return tabsList;
        }

        // public: initialize by adding default elements
        function init() {
            Array.prototype.slice.call(initEls, 0).forEach(function (el) {
                add(el, {
                    automated: el.classList.contains(defaults.automationClass)
                });
            });
        }

        return {
            add: add,
            list: list,
            init: init
        };
    }());


    //////////////////////////////
    //  shared height elements  //
    //////////////////////////////

    // usage:
    // <el class="shared-height" data-height-group="[string]" />
    // assumes box-sizing: border-box;

    var sharedHeights = (function () {
        var initEls = document.getElementsByClassName('shared-height'),
            heightGroups = {};

        // public: update all shared-height elements
        function update() {
            var g, thisGroup, heights, maxHeight;

            function resetHeight(el) {
                el.style.minHeight = 0;
                heights.push(el.offsetHeight);
            }
            function applyHeight(el) {
                el.style.minHeight = maxHeight + 'px';
            }

            for (g in heightGroups) {
                if (heightGroups.hasOwnProperty(g)) {
                    thisGroup = heightGroups[g];
                    heights = [];
                    thisGroup.forEach(resetHeight);
                    maxHeight = Math.max.apply(null, heights);
                    thisGroup.forEach(applyHeight);
                }
            }
        }

        // public: add a shared-height element
        function add(el, group) {
            if (!heightGroups[group]) {
                heightGroups[group] = [];
            }
            heightGroups[group].push(el);
        }

        // public: return heightGroups object
        function list() {
            return heightGroups;
        }

        // public: initialize with default elements
        function init() {
            Array.prototype.slice.call(initEls, 0).forEach(function (el) {
                add(el, el.getAttribute('data-height-group'));
            });
            update();
        }

        var debouncedUpdate = debounce(update, 75);
        window.addEventListener('resize', debouncedUpdate);

        return {
            add: add,
            list: list,
            update: update,
            init: init
        };
    }());


    //////////////////////
    //  initialization  //
    //////////////////////

    var init = function () {
        toggles.init();
        tabs.init();
        sharedHeights.init();
        document.documentElement.classList.remove('no-js');
        document.documentElement.classList.add('js');
    };


    //////////////
    //  public  //
    //////////////

    return {
        toggles: toggles,
        tabs: tabs,
        sharedHeights: sharedHeights,
        init: init
    };

}(window, document));

WZL.init();
