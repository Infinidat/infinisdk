from docutils import nodes
from docutils.parsers.rst import directives, Directive
import infinisdk  # pylint: disable=unused-import
import gossip


class HookListDoc(Directive):
    has_content = False
    required_arguments = 0
    optional_arguments = 0
    def run(self):
        returned = []
        for hook in sorted(gossip.get_group("infinidat.sdk").get_hooks(), key=lambda hook: hook.name):
            section = nodes.section(ids=[hook.name], names=[hook.full_name])
            self.state.document.note_explicit_target(section)
            returned.append(section)
            title = hook.full_name
            args = hook.get_argument_names()
            if args:
                title += "({})".format(", ".join(args))
            section.append(nodes.title(text=title))
            if hook.deprecated:
                section.append(nodes.paragraph(text='DEPREACTED HOOK'))
            tags_text = "Supported tags: {}".format(', '.join(sorted(hook.tags))) if hook.tags else "No supported tags"
            section.append(nodes.paragraph(text=tags_text))
            if hook.doc:
                section.append(nodes.paragraph(text=hook.doc))
        return returned


def setup(app):  # pylint: disable=unused-argument
    directives.register_directive('hook_list_doc', HookListDoc)
