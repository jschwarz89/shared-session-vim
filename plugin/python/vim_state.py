import json
import logging
import os

logger = logging.getLogger('ssvim')


class VimState(object):
    COMMAND_SEPERATOR = "0b6f83ef"

    def __init__(self):
        self.yanked_registers = {}
        self.opened_buffers = set()

        self.KEY_TO_FUNC = {
            'regcontents': self._handle_yank,
            'new': self._handle_new_buffer,
            'delete': self._handle_deleted_buffer,
            'buffers': self._handle_vim_started,
        }

    @staticmethod
    def _get_file_path(vim_cwd, filename):
        path = filename
        if not filename.startswith("/"):
            path = os.path.join(vim_cwd, filename)
        return path

    @classmethod
    def _get_vim_string(cls, commands):
        return cls.COMMAND_SEPERATOR.join(commands).encode()

    def _get_commands_for_joining(self):
        commands = []

        for register, content in self.yanked_registers.items():
            commands.append(':let @%s="%s"' % (register, content))
        for filename in self.opened_buffers:
            commands.append(':badd %s' % filename)

        logger.debug("Commands for joining: %r" % commands)
        return commands

    def _handle_yank(self, json_data):
        register = json_data['regname']
        if not register:
            register = '"'
        content = os.linesep.join(json_data['regcontents'])
        if json_data['regtype'] == "V":
            content += os.linesep

        content = content.replace("'", "''")
        content = content.replace('"', '\\"')
        self.yanked_registers[register] = content
        return [':let @%s="%s"' % (register, content)]

    def _handle_new_buffer(self, json_data):
        vim_cwd = json_data['cwd']
        filename = json_data['new']
        if not filename:
            return []

        file_path = self._get_file_path(vim_cwd, filename)
        if (filename.startswith("/usr/") and
            "vim" in filename and
            filename.endswith(".txt")):
            # Ignore vim help files
            return []
        else:
            self.opened_buffers.add(file_path)
            return [":badd %s" % file_path]

    def _handle_deleted_buffer(self, json_data):
        vim_cwd = json_data['cwd']
        filename = json_data['delete']
        if not filename:
            return []

        file_path = self._get_file_path(vim_cwd, filename)
        if file_path in self.opened_buffers:
            self.opened_buffers.remove(file_path)
            return [":bd %s" % file_path]
        else:
            return []

    def _handle_vim_started(self, json_data):
        commands = []
        vim_cwd = json_data['cwd']
        for line in json_data['buffers'].split(os.linesep):
            if not line or "No Name" in line:
                continue
            content = line.split()
            filename = content[2][1:-1]

            file_path = self._get_file_path(vim_cwd, filename)
            self.opened_buffers.add(file_path)
            commands.append(":badd %s" % file_path)
        return commands

    def get_vim_commands(self, data):
        commands_for_rest = []
        json_data = json.loads(data)

        for key, func in self.KEY_TO_FUNC.items():
            if key in json_data:
                commands_for_rest.extend(func(json_data))
                break

        logger.debug("Commands for the rest of the clients: %r" %
                     commands_for_rest)

        commands_for_joining = []
        if "buffers" in json_data:
            commands_for_joining = self._get_commands_for_joining()

        return (
            self._get_vim_string(commands_for_joining),
            self._get_vim_string(commands_for_rest)
        )
