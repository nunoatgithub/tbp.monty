from __future__ import annotations

import textwrap
from typing import Any


class REPL:
    """
    Read-Eval-Print Loop for interactive documentation queries.
    """

    def __init__(self, index_orchestrator, query_orchestrator):
        self.command_handler = CommandHandler(index_orchestrator, query_orchestrator)

    def run(self) -> None:
        self._print_welcome()

        while True:
            try:
                user_input = input("\n> ").strip()

                if not user_input:
                    continue

                # Parse and execute command
                result = self.command_handler.parse_and_execute(user_input)

                # None means exit
                if result is None:
                    print("\nGoodbye!")
                    break

                # Display result
                self._display_result(result)

            except KeyboardInterrupt:
                print("\n\nUse 'exit' or 'quit' to leave.")
                continue
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                continue

    @staticmethod
    def _print_welcome() -> None:
        """Print welcome message."""
        print("=" * 70)
        print("Monty Documentation RAG System")
        print("=" * 70)
        print("\nType 'help' for commands or ask a question.")
        print("Type 'exit' or 'quit' to leave.")

    @staticmethod
    def _display_result(result: Dict[str, Any]) -> None:
        """
        Display command result.

        Args:
            result: Result dictionary from command handler
        """
        result_type = result.get('type', 'unknown')

        if result_type == 'empty':
            return

        elif result_type == 'error':
            print(f"\n❌ Error: {result['message']}")

        elif result_type == 'help':
            print(result['text'])

        elif result_type == 'query':
            REPL._display_query_result(result)

        elif result_type == 'ingest':
            REPL._display_ingest_result(result)

        else:
            print(f"\nUnknown result type: {result_type}")

    @staticmethod
    def _display_query_result(result: Dict[str, Any]) -> None:
        print("\n" + "=" * 70)
        print("Answer:")
        print("=" * 70)

        # Wrap the answer text to 70 characters
        wrapped_answer = textwrap.fill(result['answer'], width=70)
        print(wrapped_answer)

        if result['sources']:
            print("\n" + "-" * 70)
            print("Sources:")
            print("-" * 70)
            for source in result['sources']:
                print(f"  • {source}")

        print("\n" + "-" * 70)

    @staticmethod
    def _display_ingest_result(result: Dict[str, Any]) -> None:
        stats = result['stats']

        print("\n" + "=" * 70)
        print(f"Indexing Results")
        print("=" * 70)
        print(f"Total documents: {stats['total']}")
        print(f"✓ Succeeded: {stats['succeeded']}")
        print(f"✗ Failed: {stats['failed']}")

        if stats['failed'] > 0 and 'errors' in stats:
            print("\nErrors:")
            for error in stats['errors'][:5]:  # Show first 5 errors
                print(f"  • {error}")
            if len(stats['errors']) > 5:
                print(f"  ... and {len(stats['errors']) - 5} more errors")

class CommandHandler:
    """
    Parses user input and routes to appropriate orchestrator methods.
    """

    def __init__(
        self,
        index_orchestrator,
        query_orchestrator
    ):
        self.index_orchestrator = index_orchestrator
        self.query_orchestrator = query_orchestrator

    def parse_and_execute(self, user_input: str) -> Optional[Dict[str, Any]]:

        user_input = user_input.strip()

        if not user_input:
            return {'type': 'empty'}

        # Check for exit commands
        if user_input.lower() in ['exit', 'quit']:
            return None

        # Check for help command
        if user_input.lower() == 'help':
            return self._handle_help()

        # Check for ingest commands
        if user_input.startswith('ingest'):
            return self._handle_ingest()

        # Otherwise, treat as a query
        return self._handle_query(user_input)

    def _handle_query(self, user_input: str) -> Dict[str, Any]:
        question = user_input.strip()

        try:
            result = self.query_orchestrator.query(question)
            result['type'] = 'query'
            return result
        except Exception as e:
            return {
                'type': 'error',
                'message': f"Query failed: {e}"
            }

    def _handle_ingest(self) -> Dict[str, Any]:
        stats = self.index_orchestrator.index_documents()
        return {
            'type': 'ingest',
            'stats': stats
        }

    def _handle_help(self) -> dict[str, Any]:
        """
        Handle help command.

        Returns:
            Help text dictionary
        """
        help_text = """
Available Commands:

Query Commands:
  <question>                          - Ask a question

Indexing Commands:
  ingest                              - Index all docs

Management Commands:
  help                                - Show this help message
  exit, quit                          - Exit the program

Examples:
  > What is the evidence-based learning module?

"""
        return {
            'type': 'help',
            'text': help_text
        }