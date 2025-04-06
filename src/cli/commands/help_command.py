"""
Help command implementation using the declarative approach.
"""
from typing import Optional

from .declarative import DeclarativeCommand, command


@command(name="help")
class HelpCommand(DeclarativeCommand):
    """
    Provides help information for available commands.
    """
    # Optional command name to get help for
    topic: Optional[str] = None
    
    def execute_command(self, shell) -> bool:
        """
        Execute the help command.
        
        If topic is provided, show detailed help for that command.
        Otherwise, display a list of all available commands.
        """
        if not self.topic:
            # Display list of all commands
            self._display_all_commands(shell)
        else:
            # Display help for specific command
            self._display_command_help(self.topic, shell)
        
        return True
    
    def _display_all_commands(self, shell):
        """Display help for all available commands."""
        commands = shell.command_handler.get_commands()
        unique_commands = {}
        
        # Group commands by their class to avoid duplicates
        for cmd_name, cmd_instance in commands.items():
            class_name = cmd_instance.__class__.__name__
            if class_name not in unique_commands:
                # Get the first command name as primary
                primary_name = cmd_instance.get_command_names()[0]
                unique_commands[class_name] = {
                    'instance': cmd_instance,
                    'primary_name': primary_name,
                    'aliases': cmd_instance.get_command_names()
                }
        
        # Print the help info
        print("\nAvailable commands:")
        print("===================")
        
        # Sort by primary command name
        for _, cmd_info in sorted(unique_commands.items(), key=lambda x: x[1]['primary_name']):
            primary = cmd_info['primary_name']
            aliases = [a for a in cmd_info['aliases'] if a != primary]
            alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
            
            # Get the first line of the help text
            help_text = cmd_info['instance'].get_help().split('\n')[0]
            
            print(f"  {primary}{alias_str}")
            print(f"      {help_text}")
        
        print("\nFor detailed help on a specific command, type: help <command>")
    
    def _display_command_help(self, cmd_name, shell):
        """Display detailed help for a specific command."""
        commands = shell.command_handler.get_commands()
        
        if cmd_name in commands:
            cmd = commands[cmd_name]
            all_names = cmd.get_command_names()
            primary_name = all_names[0]
            aliases = ', '.join([n for n in all_names if n != primary_name])
            
            print(f"\nHelp for command: {primary_name}")
            if aliases:
                print(f"Aliases: {aliases}")
            print("=" * (15 + len(primary_name)))
            print(cmd.get_help())
        else:
            print(f"Unknown command: {cmd_name}")


# Registering an alias for the help command ('?')
@command(name="?")
class HelpAliasCommand(HelpCommand):
    """Alias for the help command."""
    pass