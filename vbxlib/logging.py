class Singleton(type):
# from https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        else:
            cls._instances[cls].__init__(*args, **kwargs)
        return cls._instances[cls]
        

def datetime_str(timestamp=None):
# generates string with date and time
# v1.0, 2020-05-05, RTG, Vibrobox

    import datetime

    dt_string_format = '%Y-%m-%d %H:%M:%S'

    if timestamp is not None:
    
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
            
        dt_moment = datetime.datetime.fromtimestamp(timestamp)
        
    else:
        dt_moment = datetime.datetime.now()
        
    return dt_moment.strftime(dt_string_format)


class print_log(metaclass=Singleton):
# warapper for msgs output
# v1.0, 2020-05-05, RTG, Vibrobox

    def __init__(self, *args, **kvargs):

        import time

        args_list = list(args) + list(kvargs.values())
        prefix_list = ['INFO', 'DEBUG', 'WARNING', 'ERROR', 'EXCEPTION', 'TEST']
        
        if any( arg.startswith(p) \
                for arg in args_list \
                for p in prefix_list \
                if isinstance(arg, str)):
                
            if (not hasattr(self, 'last_call_time') \
                    or self.last_call_time - time.time() > 0.1):
            
                print('\n', datetime_str(), sep='', end='\n')
                
            if any( len(arg)>80 \
                    or (len(arg)>5 \
                    and '\n' in arg \
                    and not arg.endswith('\n')) \
                    for arg in args_list \
                    if isinstance(arg, str)):
                print('', sep='', end='\n')
        
        print(*args, **kvargs)

        self.last_call_time = time.time()
        
        
