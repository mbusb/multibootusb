import iso
import source


def parse(path_or_url, cache_content=False, min_fetch=16):
    """
    Returns an :class:`ISO` object for the given filesystem path or URL.

    cache_content:
      Whether to store sectors backing file content in the sector cache. If true, this will
      cause memory usage to grow to the size of the ISO as more file content get accessed.
      Even if false (default), an individual Record object will cache its own file content
      for the lifetime of the Record, once accessed.

    min_fetch:
      The smallest number of sectors to fetch in a single operation, to speed up sequential
      accesses, e.g. for directory traversal.  Defaults to 16 sectors, or 32 KiB.
    """
    if path_or_url.startswith("http"):
        src = source.HTTPSource(path_or_url, cache_content=cache_content, min_fetch=min_fetch)
    else:
        src = source.FileSource(path_or_url, cache_content=cache_content, min_fetch=min_fetch)
    return iso.ISO(src)
