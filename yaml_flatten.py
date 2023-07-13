import yaml
import sys

def data_flatten(key, value):
    path_list = []
    if key.count(".") > 0:
        key = '"%s"' % (key)
    if isinstance(value, (int, float)):
        path = "%s: %s" % (key, value)
        path_list.append(path)
    elif isinstance(value, str):
        path = "%s: \"%s\"" % (key, value)
        path_list.append(path)
    elif isinstance(value, dict) and value:
        for k in value:
            path_list.extend(data_flatten(k, value[k]))
        path_list = ["%s.%s" % (key, element) for element in path_list]
    elif isinstance(value, list):
        for i in range(len(value)):
            vlName = ""
            if isinstance(value[i], str):
                path_list.append("%s%s: %s" % (key, vlName, value[i]))
            else:
                # dict
                r = sorted(get_data_path(value[i]), reverse=True)
                for element in r:
                    if 'vlName' in element:
                        vlName = '[' + element.split(": ")[1] + ']'
                    s = "%s%s.%s" % (key, vlName, element)
                    path_list.append(s)
    # Some parameters of vdu are empty, and unknow type will appear
    else:
        path = "%s: """ % (key)
        path_list.append(path)
    #    print("unknown type")
    #    print("key value, type(value): ", key, value, type(value))
    return path_list

def get_data_path(data):
    result = []
    for key in data:
        result.extend(data_flatten(key, data[key]))
    return result

def get_key_path(data):
    result = []
    for key in data:
        result.extend(i.split(':')[0] for i in data_flatten(key, data[key]))
    return result

if __name__ == '__main__':
    with open(sys.argv[1],'r') as file:
        try:
            result = yaml.load(file, Loader=yaml.FullLoader)
        except AttributeError:
            result = yaml.load(file)
    result = get_data_path(result)
    print(result)
