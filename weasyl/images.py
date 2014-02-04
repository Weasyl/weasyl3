from sanpera.image import Image
from sanpera import geometry


read = Image.read
from_buffer = Image.from_buffer


class ThumbnailingFuckedUp(Exception):
    pass


def unanimate(im):
    if len(im) == 1:
        return im
    ret = Image()
    ret.append(im[0])
    return ret


def correct_image_and_call(f, im, *a, **kw):
    """
    Call a function, passing in an image where the canvas size of each frame is
    the same.

    The function can return an image to post-process or None.
    """

    animated = len(im) > 1
    # either of these operations make the image satisfy the contraint
    # `all(im.size == frame.size for frame in im)`
    if animated:
        im = im.coalesced()
    else:
        im = im.cropped(im[0].canvas)
    # returns a new image to post-process or None
    im = f(im, *a, **kw)
    if animated and im is not None:
        im = im.optimized_for_animated_gif()
    return im


def _resize(im, width, height):
    # resize only if we need to; return None if we don't
    if im.size.width > width or im.size.height > height:
        im = im.resized(im.size.fit_inside((width, height)))
        return im


def resize_image(im, width, height):
    return correct_image_and_call(_resize, im, width, height) or im


def make_cover_image(im):
    return resize_image(im, 1024, 3000)


def _shrinkcrop(im, size, bounds=None):
    if bounds is not None:
        ret = im
        if bounds.position != geometry.origin or bounds.size != ret.size:
            ret = ret.cropped(bounds)
        if ret.size != size:
            ret = ret.resized(size)
        return ret
    elif im.size == size:
        return im
    shrunk_size = im.size.fit_around(size)
    shrunk = im
    if shrunk.size != shrunk_size:
        shrunk = shrunk.resized(shrunk_size)
    x1 = (shrunk.size.width - size.width) // 2
    y1 = (shrunk.size.height - size.height) // 2
    bounds = geometry.Rectangle(x1, y1, x1 + size.width, y1 + size.height)
    return shrunk.cropped(bounds)


def shrinkcrop(im, size, bounds=None):
    ret = correct_image_and_call(_shrinkcrop, im, size, bounds)
    if ret.size != size or (len(ret) == 1 and ret[0].size != size):
        raise ThumbnailingFuckedUp(ret.size, ret[0].size)
    return ret
