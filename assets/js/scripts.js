var WZL = (function (window, document) {

    'use strict';

    ////////////////////////
    //  helper functions  //
    ////////////////////////

    // forEach shortcut, for use on nodelists
    function forEach(list, fn) {
        for (var idx = list.length - 1; idx >= 0; idx--) {
            fn(list[idx], idx);
        }
    }

    // copy an array, or convert a nodelist to an array
    function toArray(list) {
        return Array.prototype.slice.call(list, 0);
    }

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

    // trigger a change event on an element
    function triggerChange(el) {
        var event = document.createEvent('HTMLEvents');
        event.initEvent('change', true, false);
        el.dispatchEvent(event);
    }



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
        function create(el) {
            var result = new Toggle(el);
            toggleList.push(result);
            return result;
        }

        // public: returns an array of all toggles on the page
        function list() {
            return toggleList;
        }

        // public: initialize by adding default elements
        function init() {
            Array.prototype.slice.call(initEls, 0).forEach(function (el) {
                create(el);
            });
        }

        return {
            create: create,
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
        function create(container, options) {
            options.automated = options.automated || defaults.automated;
            options.tabSelector = options.tabSelector || defaults.tabSelector;
            options.paneSelector = options.paneSelector || defaults.paneSelector;
            options.slideDuration = options.slideDuration || defaults.slideDuration;
            var result = new TabGroup(container, options);
            tabsList.push(result);
            return result;
        }

        // public: returns array of all tab groups on the page
        function list() {
            return tabsList;
        }

        // public: initialize by adding default elements
        function init() {
            Array.prototype.slice.call(initEls, 0).forEach(function (el) {
                create(el, {
                    automated: el.classList.contains(defaults.automationClass)
                });
            });
        }

        return {
            create: create,
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
        function create(el, group) {
            if (!heightGroups[group]) {
                heightGroups[group] = [];
            }
            heightGroups[group].push(el);
            return el;
        }

        // public: return heightGroups object
        function list() {
            return heightGroups;
        }

        // public: initialize with default elements
        function init() {
            Array.prototype.slice.call(initEls, 0).forEach(function (el) {
                create(el, el.getAttribute('data-height-group'));
            });
            update();
        }

        var debouncedUpdate = debounce(update, 75);
        window.addEventListener('resize', debouncedUpdate);

        return {
            create: create,
            list: list,
            update: update,
            init: init
        };
    }());



    /////////////////////
    //  mosaics/tiles  //
    /////////////////////

    var mosaics = (function () {
        var initEls = document.getElementsByClassName('mosaic'),
            defaults = {
                blockSize: 96,
                maxBlocksPerTile: 3,
                ragged: false,
                tileClass: 'item'
            },
            mosaicList = [];

        function Mosaic(el, options) {
            // personal properties
            this.el = el;
            this.grid = [];
            this.tiles = [];
            this.maxBlockSize = options.blockSize || defaults.blockSize;
            this.maxBlocksPerTile = options.maxBlocksPerTile || defaults.maxBlocksPerTile;
            this.ragged = options.ragged || defaults.ragged;
            this.tileClass = options.tileClass || defaults.tileClass;

            // calculated properties
            this.blockSize = 0;
            this.containerWidth = 0;
            this.columns = 0;
            this.calculateProps();

            // process tiles
            this.initTiles();

            // calculate layout
            this.layout();

            // draw layout
            this.draw();

            el.classList.add('enabled');

            // see bottom of file for window resize listener
        }

        // initializes an empty grid row or set of grid rows
        Mosaic.prototype.createGridRow = function (row, endRow) {
            endRow = endRow || row;
            for (; row <= endRow; row++) {
                this.grid[row] = [];
                for (var i = 0; i < this.columns; i++) {
                    this.grid[row].push(false);
                }
            }
        };

        // calculates derived container properties
        Mosaic.prototype.calculateProps = function () {
            // avoid infinite loop that happens when we can't get width
            this.el.setAttribute('style', 'display: block !important;');
            this.el.parentNode.setAttribute('style', 'display: block !important;');
            this.containerWidth = this.el.offsetWidth;
            this.el.removeAttribute('style');
            this.el.parentNode.removeAttribute('style');

            this.columns = Math.ceil(this.containerWidth / this.maxBlockSize);
            this.blockSize = Math.floor(this.containerWidth / this.columns);
        };

        // inventory and track tiles in this container
        Mosaic.prototype.initTiles = function () {
            var that = this;
            Array.prototype.slice.call(that.el.getElementsByClassName(that.tileClass), 0)
                .forEach(function (tile) {
                    that.tiles.push(new Tile(tile, that.maxBlocksPerTile));
                });
        };

        // the good part
        Mosaic.prototype.layout = function () {
            var that = this,
                currentIndex = 0,
                isLookahead = false,
                cursorX = 0,
                cursorY = 0,
                thisTile, availableSpace, backupTile,
                foundBackupTile = false;

            // reset to a fresh slate
            this.grid.length = 0;
            this.createGridRow(0, this.maxBlocksPerTile - 1);
            if (this.ragged) {
                for (var i = 0; i < this.columns; i++) {
                    if (Math.random() < 0.5) {
                        this.grid[0][i] = true;
                        if (Math.random() < 0.4) {
                            this.grid[1][i] = true;
                        }
                    }
                }
            }
            this.tiles.forEach(function (tile) {
                tile.placed = false;
            });

            // helper: finds available space to the right of a given grid point
            function findSpaceFromPoint(x, y) {
                var availableSpace = 0,
                    offsetX;

                // reject if at end of row
                if (x >= that.columns) {
                    return [false, x];
                }
                // jump to next available space, or reject if none
                while (that.grid[y][x]) {
                    if (x >= that.columns) {
                        return [false, x];
                    }
                    x++;
                }

                // count available spaces, then return
                offsetX = x;
                while (x < that.columns) {
                    availableSpace++;
                    x++;
                    if (that.grid[y][x]) {
                        break;
                    }
                }
                return [availableSpace, offsetX];
            }

            // helper: reserves grid space for a given tile
            function placeTile(tile) {
                tile.posX = cursorX
                tile.posY = cursorY
                tile.placed = true;

                for (var i = 0; i < tile.sizeX; i++) {
                    for (var j = 0; j < tile.sizeY; j++) {
                        that.grid[cursorY + j][cursorX + i] = true;
                    }
                }
                cursorX += tile.sizeX;
            }

            // fit each tile
            while (currentIndex < this.tiles.length) {
                // if this is a lookahead, skip iterator mod
                if (isLookahead) {
                    isLookahead = false;
                // otherwise, find earliest unplaced tile
                } else {
                    currentIndex = 0;
                    for (var i = 0; i < this.tiles.length; i++) {
                        if (!this.tiles[i].placed) {
                            currentIndex = i;
                            break;
                        }
                        currentIndex++;
                    }
                }
                // extra check because we mess with iterator condition
                if (currentIndex >= this.tiles.length) {
                    break;
                }

                // some quick references
                thisTile = this.tiles[currentIndex];
                thisTile.sizeX = thisTile.maxSizeX;
                thisTile.sizeY = thisTile.maxSizeY;

                // get space available from current cursor point
                availableSpace = findSpaceFromPoint(cursorX, cursorY);

                // if we've reached the end of the row without a place, go to a new row
                while (availableSpace[0] === false || availableSpace[0] <= 0) {
                    cursorY++;
                    cursorX = 0;
                    this.createGridRow(cursorY + this.maxBlocksPerTile - 1);
                    availableSpace = findSpaceFromPoint(cursorX, cursorY);
                }
                cursorX = availableSpace[1];

                // shrink tile if needed
                while (availableSpace[0] < thisTile.sizeX && thisTile.sizeX > 1 && thisTile.sizeY > 1) {
                    if (thisTile.sizeX % 2 === 0 && thisTile.sizeY % 2 === 0) {
                        thisTile.sizeX /= 2;
                        thisTile.sizeY /= 2;
                    } else {
                        thisTile.sizeX -= 1;
                        thisTile.sizeY -= 1;
                    }
                }
                // place tile if we can
                if (availableSpace[0] >= thisTile.sizeX) {
                    placeTile(thisTile);
                // fall back if we can't place this tile
                } else {
                    // search upcoming tiles for a possible candidate
                    for (backupTile = currentIndex + 1; backupTile < this.tiles.length; backupTile++) {
                        if (!this.tiles[backupTile].placed) {
                            foundBackupTile = true;
                            break;
                        }
                    }
                    if (foundBackupTile) {
                        foundBackupTile = false;
                        isLookahead = true;
                        currentIndex = backupTile;
                        continue;
                    }
                    // if no other candidate found, make due
                    // if we can, advance the x position and try again
                    if (cursorX < this.columns) {
                        cursorX++;
                        continue;
                    }
                    // last resort, make a new row and try again
                    cursorX = 0;
                    cursorY++;
                    this.createGridRow(cursorY + this.maxBlocksPerTile - 1);
                    continue;
                }
            }
        };

        // translate grid data to css layout
        Mosaic.prototype.draw = function () {
            var that = this,
                trimLength = 0,
                halfMaxSize = Math.floor(that.maxBlocksPerTile / 2);
            
            this.tiles.forEach(function (tile) {
                tile.el.style.width = tile.sizeX * that.blockSize + 'px';
                tile.el.style.height = tile.sizeY * that.blockSize + 'px';
                tile.el.style.left = tile.posX * that.blockSize + 'px';
                tile.el.style.top = tile.posY * that.blockSize + 'px';

                // set up or reset info tooltip
                tile.tooltip.style.width = that.blockSize * that.maxBlocksPerTile + 'px';
                tile.tooltip.style.marginLeft = 0;
                tile.tooltip.classList.remove('edge-left');
                tile.tooltip.classList.remove('edge-right');

                // position info tooltip
                // left edge
                if (tile.posX <= halfMaxSize) {
                    tile.tooltip.classList.add('edge-left');
                // right edge
                } else if (tile.posX + tile.sizeX >= that.columns - halfMaxSize) {
                    tile.tooltip.classList.add('edge-right');
                // somewhere in the middle
                } else {
                    tile.tooltip.style.marginLeft = (-that.blockSize * that.maxBlocksPerTile / 2) + 'px';
                }
            });

            // set height of container to avoid colliding with layout
            for (var i = this.grid.length - 1; i >= 0; i--) {
                if (this.grid[i].indexOf(true) !== -1) {
                    break;
                }
                trimLength++;
            }
            this.el.style.height = ((this.grid.length - trimLength) * this.blockSize) + 'px';
        };

        // quick reference for refreshing the mosaic
        Mosaic.prototype.refresh = function () {
            this.calculateProps();
            this.layout();
            this.draw();
        };

        function Tile(el, maxSize) {
            this.el = el;

            // positioning properties
            this.aspect = parseFloat(el.getAttribute('data-init-aspect'));
            this.placed = false;
            this.maxSizeX = maxSize;
            this.maxSizeY = maxSize;
            this.sizeX = maxSize;
            this.sizeY = maxSize;
            this.posX = 0;
            this.posY = 0;

            // children
            this.image = el.querySelector('.thumb').getAttribute('src');
            this.anchor = el.querySelector('a');
            this.tooltip = el.querySelector('.info');

            // set image as a bg to let the browser handle sizing
            this.anchor.style.backgroundImage = 'url("' + this.image + '")';

            // assign sizing
            if (this.aspect < 1) {
                this.maxSizeX = Math.ceil(maxSize * this.aspect);
            } else if (this.aspect > 1) {
                this.maxSizeY = Math.ceil(maxSize / this.aspect);
            }
        }


        // public: add mosaic functionality to a container
        function create(el, options) {
            options = options || {};
            var result = new Mosaic(el, options);
            mosaicList.push(result);
            return result;
        }

        // public: return a list of all mosaics on page
        function list() {
            return mosaicList;
        }

        // public: initialize with default elements
        function init() {
            Array.prototype.slice.call(initEls, 0).forEach(function (el) {
                create(el, {
                    ragged: el.classList.contains('ragged')
                });
            });
        }

        return {
            create: create,
            list: list,
            init: init
        };
    }());



    //////////////////////////
    //  resizing textareas  //
    //////////////////////////

    // usage:
    // <div class="resizing-textarea">
    //      <textarea></textarea>
    // </div>

    var textareas = (function () {
        var initEls = document.getElementsByClassName('resizing-textarea'),
            textareasList = [];

        function Textarea(el) {
            this.el = el;
            this.container = getParentsByClassName(el, 'comment-new-box')[0];
            this.textarea = el.getElementsByTagName('textarea')[0];
            this.ref = document.createElement('div');

            // set up reference element
            this.ref.classList.add('resize-ref');
            this.el.appendChild(this.ref);

            // initial update + update on change
            this.update();
            this.textarea.addEventListener('input', this.update.bind(this));

            // comment entry focus viz
            if (this.container) {
                this.textarea.addEventListener('focus', this.highlight.bind(this));
                this.textarea.addEventListener('blur', this.unhighlight.bind(this));
            }
        }

        // updates this textarea size
        Textarea.prototype.update = function () {
            // append additional space and break so IE respects any trailing whitespace
            this.ref.innerHTML = this.textarea.value.replace(/\n/g, '<br />') + ' <br />&#160;';
        };

        Textarea.prototype.highlight = function () {
            this.container.classList.add('highlight');
        };

        Textarea.prototype.unhighlight = function () {
            if (this.textarea.value.length === 0) {
                this.container.classList.remove('highlight');
            }
        };

        // public: add a resizing textarea
        function create(el) {
            var result = new Textarea(el);
            textareasList.push(result);
            return result;
        }

        // public: list all resizing textareas on page
        function list() {
            return textareasList;
        }

        // public: initialize with default elements
        function init() {
            Array.prototype.slice.call(initEls, 0).forEach(function (el) {
                create(el);
            });
        }

        return {
            create: create,
            list: list,
            init: init
        };
    }());



    //////////////////////////
    //  active form labels  //
    //////////////////////////

    // usage:
    // <label class="active-label">
    //      <span>label text</span>
    //      <input />
    // </label>

    var activeLabels = (function () {
        var initEls = document.getElementsByClassName('active-label'),
            labelsList = [];

        // public: make an label active
        function create(el) {
            var input = el.getElementsByTagName('input')[0] ||
                el.getElementsByTagName('textarea')[0];

            function checkFilled() {
                if (input.value !== '') {
                    el.classList.add('has-contents');
                } else {
                    el.classList.remove('has-contents');
                }
            }

            checkFilled();
            input.addEventListener('focus', function () {
                el.classList.add('active');
            });
            input.addEventListener('blur', function () {
                el.classList.remove('active');
                checkFilled();
            });

            el.classList.add('enabled');

            labelsList.push(el);
            return el;
        }

        // public: list active labels on page
        function list() {
            return labelsList;
        }

        // public: initialize with default elements
        function init() {
            Array.prototype.slice.call(initEls, 0).forEach(function (el) {
                create(el);
            });
        }

        return {
            create: create,
            list: list,
            init: init
        };
    }());



    /////////////////////////////
    //  checkbox/radio events  //
    /////////////////////////////

    // tracks checkboxes for counts, hierarchies, and active/inactive labels
    // in addition, covers check/uncheck/invert all functions

    var checkboxes = (function () {
        var initEls = document.querySelectorAll('input[type=checkbox], input[type=radio]'),
            initHierarchies = document.getElementsByClassName('checkbox-group'),
            initDrivers = document.querySelectorAll('.check-all, .uncheck-all, .invert-all'),
            countEls = document.getElementsByClassName('checked-count');

        // returns checkboxes within given context that are valid for counting
        function getCheckboxes(context) {
            return Array.prototype.slice.call(
                context.querySelectorAll('input[type="checkbox"]'),
                0
            ).filter(function (el) {
                return !el.classList.contains('checkbox-parent');
            });
        }

        // returns true if all elements in a given set are :checked
        function areAllChecked(els) {
            return Array.prototype.slice.call(els, 0).every(function (el) {
                return el.checked;
            });
        }

        // counts the number of checked elements inside the context of a given count element
        function updateCounts() {
            Array.prototype.slice.call(countEls, 0).forEach(function (el) {
                var checkboxes = getCheckboxes(document.querySelector(el.getAttribute('data-context'))),
                    count = checkboxes.reduce(function (sum, el) {
                        return sum + el.checked;
                    }, 0);
                el.textContent = count + ' of ' + checkboxes.length;
            });
        }

        // things that should happen on generic checkbox click
        function updateLabel(el) {
            var label = getParentsByTagName(el, 'label')[0];
            if (el.checked) {
                label.classList.add('checked');
            } else {
                label.classList.remove('checked');
            }
        }

        function CheckboxGroup(el) {
            var that = this;

            this.container = el;
            this.children = Array.prototype.slice.call(el.getElementsByClassName('checkbox-child'), 0);
            this.main = el.getElementsByClassName('checkbox-parent')[0];

            this.children.forEach(function (el) {
                el.addEventListener('change', function () {
                    that.main.checked = areAllChecked(that.children);
                    triggerChange(that.main);
                });
            });
            this.main.addEventListener('click', function () {
                var thisChecked = this.checked;
                that.children.forEach(function (el) {
                    el.checked = thisChecked;
                    triggerChange(el);
                });
            });
        }

        // public: start tracking checkbox or radio button
        function create(el) {
            updateLabel(el);
            el.addEventListener('change', function () {
                updateLabel(this);
                updateCounts();
            });
            return el;
        }

        // public: start tracking hierarchy group
        function createHierarchy(el) {
            return new CheckboxGroup(el);
        }

        // public: add en element that effects all checkboxes in given context
        function createDriver(el, context, state) {
            var checkboxes = getCheckboxes(context);
            if (state === 'inverse') {
                el.addEventListener('click', function () {
                    checkboxes.forEach(function (thisCheckbox) {
                        thisCheckbox.checked = !thisCheckbox.checked;
                        triggerChange(thisCheckbox);
                    });
                });
            } else {
                el.addEventListener('click', function () {
                    checkboxes.forEach(function (thisCheckbox) {
                        thisCheckbox.checked = state;
                        triggerChange(thisCheckbox);
                    });
                });
            }
        }

        // public: initialize with default elements
        function init() {
            Array.prototype.slice.call(initEls, 0).forEach(function (el) {
                create(el);
            });
            Array.prototype.slice.call(initHierarchies, 0).forEach(function (el) {
                createHierarchy(el);
            });
            Array.prototype.slice.call(initDrivers, 0).forEach(function (el) {
                var context = document.querySelector(el.getAttribute('data-context')),
                    state;
                if (el.classList.contains('check-all')) {
                    state = true;
                } else if (el.classList.contains('uncheck-all')) {
                    state = false;
                } else if (el.classList.contains('invert-all')) {
                    state = 'inverse';
                }
                createDriver(el, context, state);
            });
            updateCounts();
        }

        return {
            create: create,
            createHierarchy: createHierarchy,
            createDriver: createDriver,
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
        mosaics.init();
        textareas.init();
        activeLabels.init();
        checkboxes.init();
        document.documentElement.classList.remove('no-js');
        document.documentElement.classList.add('js');
    };







    ////////////////////////
    //  crud to clean up  //
    ////////////////////////

/*
    // helper function: nodelist to array
    function toArray(obj) {
        var array = [];
        for (var i = obj.length >>> 0; i--;) {
            array[i] = obj[i];
        }
        return array;
    }

    // debounced window resize event
    (function() {
        if (!window.addEventListener || !document.createEvent) {
            return;
        }

        var event = document.createEvent('Event');
        event.initEvent('resize:end', false, false);

        function dispatchResizeEndEvent() {
            return window.dispatchEvent(event);
        }

        var initialOrientation = window.orientation;
        var resizeDebounceTimeout = null;

        function debounce() {
            var currentOrientation = window.orientation;

            if (currentOrientation !== initialOrientation) {
                dispatchResizeEndEvent();
                initialOrientation = currentOrientation;
            } else {
                clearTimeout(resizeDebounceTimeout);
                resizeDebounceTimeout = setTimeout(dispatchResizeEndEvent, 100);
            }
        }

        window.addEventListener('resize', debounce, false);
    })();


    // art zoom
    Array.prototype.forEach.call(document.getElementsByClassName('sub-zoom-toggle'), function (el) {
        el.addEventListener('click', function(ev) {
            ev.preventDefault();
            el.classList.toggle('active');
            document.querySelector('.page-header').classList.toggle('hide');
            document.querySelector('.page-footer').classList.toggle('hide');
            var artSiblings = document.getElementById('main').children;
            for ( var i = 0; i < artSiblings.length; i++ ) {
                if ( !artSiblings[i].classList.contains('sub-container') ) {
                    artSiblings[i].classList.toggle('hide');
                }
            }
            document.body.classList.toggle('zoomed');
        });
    });


    // modal escape listener
    (function() {
        var modals = document.getElementsByClassName('modal');
        if ( modals.length > 0 ) {
            window.addEventListener('keydown', function(ev) {
                if ( ev.keyCode === 27 ) {
                    for ( var i = 0; i < modals.length; i++ ) {
                        modals[i].classList.remove('active');
                    }
                }
            });
        }
    })();


    // sticky notification utilities
    // remove once position: sticky is supported 'enough'
    (function() {
        var el = document.getElementsByClassName('sticky')[0],
            mainCol = document.getElementsByClassName('col-layout-main')[0],
            footer = document.getElementsByClassName('page-footer')[0],
            refPos, elHeight, footerPos;

        if (!el || !mainCol || !footer) {
            return;
        }

        function checkSticky() {
            refPos = mainCol.getBoundingClientRect().top;
            footerPos = footer.getBoundingClientRect().top;

            if (refPos <= 0) {
                el.classList.add('stuck');
            } else {
                el.classList.remove('stuck');
            }
            if (footerPos < elHeight) {
                el.classList.add('blocked');
            } else {
                el.classList.remove('blocked');
            }
        }

        function setup() {
            elHeight = el.offsetHeight;
            mainCol.style.minHeight = elHeight + 'px';
            checkSticky();
        }

        window.addEventListener('load', setup);
        window.addEventListener('resize:end', setup, false);
        document.addEventListener('scroll', checkSticky);
    })();


    // show password fields
    Array.prototype.forEach.call(document.getElementsByClassName('show-password'), function (el) {
        var targetEls = document.querySelectorAll(el.getAttribute('data-target'));

        el.addEventListener('click', function(ev) {
            ev.preventDefault();

            var isActive = el.classList.toggle('active');

            Array.prototype.forEach.call(targetEls, function (targetEl) {
                targetEl.type = isActive ? 'text' : 'password';
            });
        });
    });
    


*/


    ////////////////////////
    //  events on window  //
    ////////////////////////

    window.addEventListener('resize', debounce(function () {
        mosaics.list().forEach(function (mosaic) {
            mosaic.refresh();
        });
    }, 400));




    //////////////
    //  public  //
    //////////////

    return {
        toggles: toggles,
        tabs: tabs,
        sharedHeights: sharedHeights,
        mosaics: mosaics,
        textareas: textareas,
        activeLabels: activeLabels,
        checkboxes: checkboxes,
        init: init
    };

}(window, document));

WZL.init();
