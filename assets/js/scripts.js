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







    ////////////////////////
    //  crud to clean up  //
    ////////////////////////

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


    // weasyl mosaic thumbnail layout
    function wzlMosaic(el) {
        var maxBlockWidth = 96,
            aspectRatios = [0.33, 0.66, 1, 1.5, 3],
            grid = [],
            tiles, tileCount, containerWidth, blockDim, columnCount, globalOffset;

        el.classList.add('enabled');

        // create a new grid row of empty cells at specified y position
        function newGridRow(row) {
            grid[row] = [];
            for ( var i = 0; i < columnCount; i++ ) {
                grid[row].push(0);
            }
            console.log('created new grid row at ' + row);
        }

        // set up container properties
        function setupContainer() {
            console.log('setting up container...');
            globalOffset = 0;

            el.setAttribute('style', 'display: block !important;');  // infinite loop if no width to go on
            el.parentNode.setAttribute('style', 'display: block !important;');
            containerWidth = el.offsetWidth;
            el.removeAttribute('style');
            el.parentNode.removeAttribute('style');

            console.log('container width: ' + containerWidth);
            columnCount = Math.ceil(containerWidth / maxBlockWidth);
            blockDim = Math.floor(containerWidth / columnCount);

            // wipe existing grid (if any) and create three empy grid rows to work within
            grid.length = 0;
            console.log('wiped existing grid');
            newGridRow(0); newGridRow(1); newGridRow(2);
            console.log('created starter rows');

            // ragged top - randomize layout of first two rows
            if ( el.classList.contains('ragged') ) {
                for (var d = 0; d < columnCount; d++) {
                    if (Math.random() < 0.5) {
                        grid[0][d] = 1;
                        if (Math.random() < 0.4) {
                            grid[1][d] = 1;
                        }
                    }
                }
                console.log('created ragged gaps');
            }
        }

        // process tile properties
        function setupTiles(offset) {
            console.log('setting up tiles ...');
            if ( !offset ) { offset = 0; }
            tiles = toArray(el.getElementsByClassName('item'));
            tileCount = tiles.length;
            console.log(tileCount + ' tiles in set');

            var offsetTiles = tiles.slice(offset);
            for ( var i = 0; i < offsetTiles.length; i++ ) {
                var thisTile = offsetTiles[i],
                    aspectRatio = parseFloat(thisTile.getAttribute('data-init-aspect')),
                    closestRatio = null,
                    thumbImage = thisTile.querySelector('.thumb').getAttribute('src'),
                    childA = thisTile.querySelector('a');
                console.log('Processing the following tile:');
                console.log(thisTile);

                // set as background image in order to let the browser handle sizing
                childA.style.backgroundImage = 'url("' + thumbImage + '")';
                console.log('backgroundImage set');

                // assign closest aspect
                for ( var j = 0; j < aspectRatios.length; j++ ) {
                    if (closestRatio === null || Math.abs(aspectRatios[j] - aspectRatio) < Math.abs(closestRatio - aspectRatio)) {
                        closestRatio = aspectRatios[j];
                    }
                }
                thisTile.setAttribute('data-snapped-aspect', closestRatio);
                thisTile.setAttribute('data-placed', 0);
                console.log('aspect ratio set: ' + closestRatio);

                // assign cell dimensions and denote resizeability
                if (closestRatio === 0.33) {
                    thisTile.setAttribute('data-sizeX', 1);
                    thisTile.setAttribute('data-sizeY', 3);
                    thisTile.setAttribute('data-resizeable2', 0);
                    thisTile.setAttribute('data-resizeable1', 0);
                } else if (closestRatio === 0.66) {
                    thisTile.setAttribute('data-sizeX', 2);
                    thisTile.setAttribute('data-sizeY', 3);
                    thisTile.setAttribute('data-resizeable2', 0);
                    thisTile.setAttribute('data-resizeable1', 1);
                    thisTile.setAttribute('data-size1X', 1);
                    thisTile.setAttribute('data-size1Y', 2);
                } else if (closestRatio === 1) {
                    thisTile.setAttribute('data-sizeX', 3);
                    thisTile.setAttribute('data-sizeY', 3);
                    thisTile.setAttribute('data-resizeable2', 1);
                    thisTile.setAttribute('data-size2X', 2);
                    thisTile.setAttribute('data-size2Y', 2);
                    thisTile.setAttribute('data-resizeable1', 1);
                    thisTile.setAttribute('data-size1X', 1);
                    thisTile.setAttribute('data-size1Y', 1);
                } else if (closestRatio === 1.5) {
                    thisTile.setAttribute('data-sizeX', 3);
                    thisTile.setAttribute('data-sizeY', 2);
                    thisTile.setAttribute('data-resizeable2', 1);
                    thisTile.setAttribute('data-size2X', 2);
                    thisTile.setAttribute('data-size2Y', 1);
                    thisTile.setAttribute('data-resizeable1', 0);
                } else if (closestRatio === 3) {
                    thisTile.setAttribute('data-sizeX', 3);
                    thisTile.setAttribute('data-sizeY', 1);
                    thisTile.setAttribute('data-resizeable2', 0);
                    thisTile.setAttribute('data-resizeable1', 0);
                }
                console.log('cell data applied to tile');
            }
        }

        // the fun part
        function mosaicLayout(isAppend) {
            console.log('Fitting tiles ...');
            var curTile = 0,
                isLookahead = false,
                posX = 0,
                posY = 0;

            // if appending to existing data, find starting row
            if (isAppend) {
                for ( var i = grid.length - 1; i >= 0; i-- ) {
                    if ( grid[i].indexOf(0) !== -1) {
                        posY = i;
                    } else {
                        break;
                    }
                }
            }

            // function to find empty spaces to the right of a given point
            function findSpaceFromPoint(posX, posY) {
                console.log('Finding space from ' + posX + ', ' + posY + ' ...');
                if (posX >= columnCount) {
                    return [false, posX];
                }
                var availableSpace = 0;

                while ( grid[posY][posX] === 1 ) {
                    if (posX >= columnCount) {
                        return [false, posX];
                    }
                    posX++;
                }
                var shiftedX = posX;

                while (posX < columnCount) {
                    availableSpace++;
                    posX++;
                    if ( grid[posY][posX] === 1 ) {
                        break;
                    }
                }

                console.log('space available: ' + availableSpace);
                return [availableSpace, shiftedX];
            }

            // function to place a tile into the grid
            function placeTile(t) {
                console.log('Placing tile into the grid ...');
                tiles[t].setAttribute('data-tilePosX', posX);
                tiles[t].setAttribute('data-tilePosY', posY);
                tiles[t].setAttribute('data-placed', 1);

                for (var i = 0; i < tileSizeX; i++) {
                    for (var j = 0; j < tileSizeY; j++) {
                        var fitX = posX + i,
                            fitY = posY + j;
                        grid[fitY][fitX] = 1;
                    }
                }

                posX += tileSizeX;
            }

            // walk through and fit each tile
            while (curTile < tileCount) {
                console.log('fitting a tile ...');

                if (isLookahead) {
                    isLookahead = false;
                } else {
                    curTile = 0;
                    for (var a = 0; a < tileCount; a++) {
                        var aa = tiles[a].getAttribute('data-placed');
                        if ( aa < 1 ) {
                            curTile = a;
                            break;
                        }
                        curTile++;
                    }
                }
                // because we mess with the iterated var
                if (curTile >= tileCount) {
                    break;
                }

                var thisTile = tiles[curTile],
                    tileSizeX = parseInt(thisTile.getAttribute('data-sizeX')),
                    tileSizeY = parseInt(thisTile.getAttribute('data-sizeY'));

                // get space available right now
                console.log('tile dimensions: ' + tileSizeX + ', ' + tileSizeY);
                var spaceAvail = findSpaceFromPoint(posX, posY);

                // if reached end of row without finding space
                while (spaceAvail[0] === false || spaceAvail[0] <= 0) {
                    posY++;
                    posX = 0;
                    newGridRow(posY + 2);
                    spaceAvail = findSpaceFromPoint(posX, posY);
                }
                posX = spaceAvail[1];

                // can this fit?
                if ( tileSizeX <= spaceAvail[0] ) {
                    console.log('found space');
                    placeTile(curTile);
                } else if ( spaceAvail[0] >= 2 && thisTile.getAttribute('data-resizeable2') == 1 ) {
                    console.log('shrank tile to 2 units wide');
                    tileSizeX = parseInt(thisTile.getAttribute('data-size2X'));
                    tileSizeY = parseInt(thisTile.getAttribute('data-size2Y'));
                    thisTile.setAttribute('data-sizeX', tileSizeX);
                    thisTile.setAttribute('data-sizeY', tileSizeY);
                    placeTile(curTile);
                } else if ( spaceAvail[0] >= 1 && thisTile.getAttribute('data-resizeable1') == 1 ) {
                    console.log('shrank tile to 1 unit wide');
                    tileSizeX = parseInt(thisTile.getAttribute('data-size1X'));
                    tileSizeY = parseInt(thisTile.getAttribute('data-size1Y'));
                    thisTile.setAttribute('data-sizeX', tileSizeX);
                    thisTile.setAttribute('data-sizeY', tileSizeY);
                    placeTile(curTile);
                } else {
                    console.log('didn’t find space');
                    var b = 0;
                    var foundTile = false;
                    for ( b = curTile + 1; b < tileCount; b++ ) {
                        if ( tiles[b].getAttribute('data-placed') < 1 ) {
                            foundTile = true;
                            break;
                        }
                    }
                    if (foundTile) {
                        console.log('looking ahead ... ');
                        foundTile = false;
                        isLookahead = true;
                        curTile = b;
                        continue;
                    }
                    // if didn't find a suitable tile, do what we can with remaining space
                    if (posX < columnCount) {
                        console.log('advancing x position, trying again');
                        posX++;
                        continue;
                    } else {
                        console.log('making new row, trying again');
                        posX = 0;
                        posY++;
                        newGridRow(posY + 2);
                        continue;
                    }
                }
            }
        }

        // place each tile into css layout
        function drawTiles(offset) {
            console.log('placing tiles into css layout ...');
            if (!offset) {
                offset = 0;
            }

            for ( var i = offset; i < tileCount; i++ ) {
                var thisTile = tiles[i],
                    thisInfo = thisTile.querySelector('.info'),
                    thisWidth = parseInt(thisTile.getAttribute('data-sizeX')) * blockDim,
                    thisHeight = parseInt(thisTile.getAttribute('data-sizeY')) * blockDim,
                    thisPosX = parseInt(thisTile.getAttribute('data-tilePosX')) * blockDim,
                    thisPosY = parseInt(thisTile.getAttribute('data-tilePosY')) * blockDim;
                console.log(thisTile);

                thisTile.style.width = thisWidth + 'px';
                thisTile.style.height = thisHeight + 'px';
                thisTile.style.left = thisPosX + 'px';
                thisTile.style.top = thisPosY + 'px';
                console.log('applied style attributes');

                // position info tooltips
                thisInfo.style.width = (blockDim * 3) + 'px';
                thisInfo.style.marginLeft = 0;
                thisInfo.classList.remove('edge-left');
                thisInfo.classList.remove('edge-right');

                if ( thisPosX < blockDim ) {
                    thisInfo.classList.add('edge-left');
                } else if ( containerWidth - thisPosX - thisWidth < blockDim ) {
                    thisInfo.classList.add('edge-right');
                } else {
                    thisInfo.style.marginLeft = (-blockDim * 3/2) + 'px';
                }
                console.log('positioned info tooltip');

                globalOffset++;
            }

            // trim grid
            console.log('trimming excess grid rows ...');
            var trimLength = 0;
            for (var n = grid.length - 1; n >= 0; n--) {
                if (grid[n].indexOf(1) !== -1) {
                    break;
                }

                trimLength++;
            }
            console.log('grid trimmed');
            // and set height of container
            el.style.height = ((grid.length - trimLength) * blockDim) + 'px';
            console.log('container height set');

            // for (var k = 0; k < grid.length; k++) {
            //     console.log(grid[k]);
            // }
        }

        // light the fuse
        console.log('starting initial run ...');
        setupContainer();
        setupTiles();
        mosaicLayout();
        drawTiles();

        // recalculate on resize
        window.addEventListener('resize:end', function() {
            console.log('resize event detected, recalculating mosaic ...');
            setupContainer();
            setupTiles();
            mosaicLayout();
            drawTiles();
        }, false);

        // hover intent
        var hoverDelay, hoverDebounce = false;
        el.addEventListener('mouseenter', function() {
            if ( !hoverDebounce ) {
                hoverDebounce = true;
                hoverDelay = setTimeout(function() {
                    el.classList.add('hovered');
                }, 940);
            }
        });
        console.log('added mouseenter handler');
        el.addEventListener('mouseleave', function() {
            hoverDebounce = false;
            clearTimeout(hoverDelay);
            el.classList.remove('hovered');
        });
        console.log('added mouseleave handler');
    }

    // active form labels
    function wzlLabels(el) {
        var input = el.getElementsByTagName('input')[0] || el.getElementsByTagName('textarea')[0];
        el.classList.add('enabled');
        function checkFilled() {
            if ( input.value !== '' ) {
                el.classList.add('has-contents');
            } else {
                el.classList.remove('has-contents');
            }
        }
        checkFilled();
        window.addEventListener('load', checkFilled);

        input.addEventListener('focus', function() {
            el.classList.add('active');
        });
        input.addEventListener('blur', function() {
            el.classList.remove('active');
            checkFilled();
        });
    }


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


    // resizing textareas
    function textareas(parentEl) {
        var el = parentEl.getElementsByTagName('textarea')[0],
            ref = parentEl.getElementsByClassName('resize-ref')[0],
            container = getParentsByClassName(el, 'comment-new-box')[0];

        function doCopy() {
            // copies textarea value to reference element
            // appends additional <br /> so IE respects trailing whitespace
            ref.innerHTML = el.value.replace(/\n/g, '<br />') + ' <br /> ';
        }
        doCopy();

        el.addEventListener('input', doCopy, false);

        // adds appropriate class to container element for focus visualization
        if (container) {
            el.addEventListener('focus', function() {
                container.classList.add('highlight');
            });
            el.addEventListener('blur', function() {
                if (el.value.length === 0) {
                    container.classList.remove('highlight');
                }
            });
        }
    }

    Array.prototype.forEach.call(document.getElementsByClassName('resizing-textarea'), function (el) {
        textareas(el);
    });


    // checkbox/radio events
    function areAllChecked(els) {  // returns true if all elements in given set are checked
        for (var i = els.length >>> 0; i--;) {
            if (els[i].checked === false) {
                return false;
            }
        }
        return true;
    }
    function getCheckboxes(context) {  // gets valid checkboxes in given context
        return toArray(context.querySelectorAll('input[type="checkbox"]:not(.checkbox-parent)'));
    }
    function updateCounts() {  // updates count elements with number of checked boxes in context
        Array.prototype.forEach.call(document.getElementsByClassName('checked-count'), function (el) {
            var checkboxes = getCheckboxes(document.querySelector(el.getAttribute('data-context')));

            var count = checkboxes.reduce(function (count, checkbox) {
                return count + checkbox.checked;
            }, 0);

            el.textContent = count + ' of ' + checkboxes.length;
        });
    }
    updateCounts();
    function triggerChange(el) {  // trigger events that fire on checkbox change
        var event = document.createEvent('HTMLEvents');
        event.initEvent('change', true, false);
        el.dispatchEvent(event);
    }
    function changeCheckboxStates(context, action) {  // change all checkboxes in context with given action
        var checkboxes = getCheckboxes(context);
        Array.prototype.forEach.call(checkboxes, function (checkbox) {
            if (action === 'on' && !checkbox.checked) {
                checkbox.checked = true;
                triggerChange(checkbox);
            } else if (action === 'off' && checkbox.checked) {
                checkbox.checked = false;
                triggerChange(checkbox);
            } else if (action === 'invert') {
                checkbox.checked = !checkbox.checked;
                triggerChange(checkbox);
            }
        });
        updateCounts();
    }
    function changeParentLabel(el) {
        var thisLabel = getParentsByTagName(el, 'label')[0];
        thisLabel.classList.toggle('checked', el.checked);
    }
    // handle individual checkbox changes
    Array.prototype.forEach.call(document.querySelectorAll('input[type=checkbox], input[type=radio]'), function (el) {
        var isParent = el.classList.contains('checkbox-parent'),
            isChild = el.classList.contains('checkbox-child');

        changeParentLabel(el);

        el.addEventListener('change', function() {
            // hierarchical checkboxes
            if ( isParent || isChild ) {
                var groupEl = getParentsByClassName(el, 'checkbox-group')[0],
                    parentBox = groupEl.getElementsByClassName('checkbox-parent')[0],
                    childBoxes = groupEl.getElementsByClassName('checkbox-child');

                if ( isParent ) {
                    Array.prototype.forEach.call(childBoxes, function (childEl) {
                        childEl.checked = el.checked;
                    });
                } else if ( !el.checked ) {
                    parentBox.checked = false;
                } else if (areAllChecked(childBoxes)) {
                    parentBox.checked = true;
                }

                Array.prototype.forEach.call([parentBox].concat(toArray(childBoxes)), function (thisBox) {
                    changeParentLabel(thisBox);
                });

            // standalone checkboxes
            } else {
                changeParentLabel(el);
            }
            updateCounts();
        });
    });
    // handle check/uncheck/invert all
    Array.prototype.forEach.call(document.querySelectorAll('.check-all, .uncheck-all, .invert-all'), function (el) {
        var context = document.querySelector(el.getAttribute('data-context'));
        if (context) {
            if (el.classList.contains('check-all')) {
                el.addEventListener('click', function() {
                    changeCheckboxStates(context, 'on');
                });
            } else if (el.classList.contains('uncheck-all')) {
                el.addEventListener('click', function() {
                    changeCheckboxStates(context, 'off');
                });
            } else if (el.classList.contains('invert-all')) {
                el.addEventListener('click', function() {
                    changeCheckboxStates(context, 'invert');
                });
            }
        }
    });


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


    Array.prototype.forEach.call(document.getElementsByClassName('mosaic'), wzlMosaic);
    Array.prototype.forEach.call(document.getElementsByClassName('active-label'), wzlLabels);








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
