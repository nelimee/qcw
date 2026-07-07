import xacc
import logging

logger = logging.getLogger(__file__)


def xacc2openqasm2(routine: xacc.CompositeInstruction) -> str:
    """Transform the given XACC routine into an OpenQASM 2.0 string."""
    logger.warn(
        "Using XACC 'staq' compiler to perform XACC -> OpenQASM 2.0 "
        "conversion. The 'staq' compiler is know to produce invalid OpenQASM "
        "2.0 when some features are used (classical if on individual bits of "
        "a classical register for example)."
    )
    openqasm2_compiler = xacc.getCompiler("staq")
    return openqasm2_compiler.translate(routine).replace("\\", "")
