from ubuntutweak import system

def is_ubuntu(distro):
    if type(distro) != list:
        return bool(system.is_supported(distro))
    for dis in distro:
        return bool(system.is_supported(dis))

def filter_sources():
    newsource = []
    for item in SOURCES_DATA:
        distro = item[1]
        if is_ubuntu(distro):
            if system.codename in distro:
                newsource.append([item[0], system.codename, item[2], item[3]])
        else:
            newsource.append(item)

    return newsource
