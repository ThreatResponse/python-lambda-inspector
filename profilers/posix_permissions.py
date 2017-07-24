import os
import stat

class PosixPermissions():

    """For getting a tree of what filesystem locations are writable."""
    
    def __init__(self):
        self.my_uid = os.getuid()
        self.my_groups = os.getgroups()
    
    def _folders_in(self, path):
        return [os.path.join(path, f) for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]

    def _octal_is_writable(self, s):
        """
        Given a 1-digit octal entry, determines if it's writable at all
        """
        writable_octals = [2, 3, 6, 7]
        return s in writable_octals

    def _octal_is_executable(self, s):
        """
        Given a 1-digit octal entry, determines if it's executable"
        """
        execable_octals = [1, 3, 5, 7]
        return s in execable_octals

    def _octal_is_readable(self, s):
        readable_octals = [4, 5, 6, 7]
        return s in readable_octals

    def check_octals_in_path(self, path, fn):
        try:
            path_stat = os.stat(path)
        except OSError:
            ## If the file doesn't exist, eg /proc items
            return False
            
        path_mode = stat.S_IMODE(path_stat.st_mode)
        path_gid = path_stat.st_gid
        path_uid = path_stat.st_uid
    
        path_mode_owner = path_mode / 64 % 8
        path_mode_group = path_mode / 8 % 8
        path_mode_all = path_mode % 8

        ## owner
        if fn(path_mode_owner):
            if self.my_uid == path_uid:
                return True
    
        ## group
        if fn(path_mode_group):
            for gid in self.my_groups:
                if gid == path_gid:
                    return True
    
        ## everyone
        if fn(path_mode_all):
            return True
    
        return False

    def path_is_writable(self, path):
        return self.check_octals_in_path(path, self._octal_is_writable)

    def path_is_execable(self, path):
        return self.check_octals_in_path(path, self._octal_is_executable)

    def path_is_readable(self, path):
        return self.check_octals_in_path(path, self._octal_is_readable)

    def get_folder_permission_tree(self, path):
        is_writable = self.path_is_writable(path)
        is_execable = self.path_is_execable(path)
        is_readable = self.path_is_readable(path)
        res = {path: {'is_writable': is_writable}}
    
        if is_execable and is_readable:
            subfolders = self._folders_in(path)
    
            if subfolders:
                res[path]['subfolders'] = [self.get_folder_permission_tree(f) for f in subfolders]
    
        return res

    def list_of_writable_paths_in_path(self, path):
        is_writable = self.path_is_writable(path)
        is_execable = self.path_is_execable(path)
        is_readable = self.path_is_readable(path)
        paths = []

        if is_writable:
            paths.append(path)
        
        if is_readable and is_execable:
            for p in self._folders_in(path):
                paths += self.list_of_writable_paths_in_path(p)

        return paths

    def most_writable_paths(self):
        """
        Not 'all writable paths' because we emit some folders
        such as /proc and /dev."
        """
        path_set = ["/bin", "/boot", "/builddir", "/etc", "/home", "/lib", "/lib64", "/media", "/mnt", "/opt", "/root", "/sbin", "/selinux", "/srv", "/tmp", "/usr", "/var"]

        paths = []
        for p in path_set:
            paths += self.list_of_writable_paths_in_path(p)

        return paths


