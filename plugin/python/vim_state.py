import json
import logging
import os
import re

logger = logging.getLogger('ssvim')


class VimState(object):
    COMMAND_SEPERATOR = "0b6f83ef"
    BUFFER_LINE_MATCHER = re.compile(
        '\s*\d+ (?P<modifiers>.+) "(?P<bufname>.*)"\s+line \d+')

    def __init__(self):
        self.yanked_registers = {}
        self.opened_buffers = set()

        self.KEY_TO_FUNC = {
            'regcontents': self._handle_yank,
            'new': self._handle_new_buffer,
            'edit': self._handle_editted_buffer,
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

    @staticmethod
    def _should_ignore_filename(filename):
        return (filename.startswith("/usr/") and
                "vim" in filename and
                filename.endswith(".txt"))

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
        if self._should_ignore_filename(filename):
            return []
        else:
            self.opened_buffers.add(file_path)
            return [":badd %s" % file_path]

    def _handle_editted_buffer(self, json_data):
        vim_cwd = json_data['cwd']
        filename = json_data['edit']
        if not filename:
            return []

        file_path = self._get_file_path(vim_cwd, filename)
        if self._should_ignore_filename(filename):
            return []
        else:
            return [":edit %s" % file_path]

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
            match = self.BUFFER_LINE_MATCHER.search(line)
            if not match:
                continue

            filename = match.group("bufname")
            file_path = self._get_file_path(vim_cwd, filename)
            self.opened_buffers.add(file_path)
            commands.append(":badd %s" % file_path)
        return commands

    def _handle_vim_command(self, command):
        commands_for_rest = []

        for key, func in self.KEY_TO_FUNC.items():
            if key in command:
                commands_for_rest.extend(func(command))
                break

        logger.debug("Commands for the rest of the clients: %r" %
                     commands_for_rest)

        commands_for_joining = []
        if "buffers" in command:
            commands_for_joining = self._get_commands_for_joining()

        return commands_for_joining, commands_for_rest

    def get_vim_commands(self, data):
        try:
            commands = [json.loads(data)]
        except json.decoder.JSONDecodeError:
            # Maybe there are multiple commands...
            raw_commands = data.split("}" + os.linesep + "{")

            commands = []
            for command in raw_commands:
                command = command.strip()
                if not command.startswith("{"):
                    command = "{%s" % command
                if not command.endswith("}"):
                    command = "%s}" % command
                commands.append(json.loads(command))

        commands_for_joining = []
        commands_for_rest = []

        for command in commands:
            joining, rest = self._handle_vim_command(command)

            commands_for_joining.extend(joining)
            commands_for_rest.extend(rest)

        return (
            self._get_vim_string(commands_for_joining),
            self._get_vim_string(commands_for_rest)
        )
