/*********************************************/
// Authors			: 	Andrea Galimberti (andrea.galimberti@polimi.it),
//                      Davide Galli (davide.galli@polimi.it),
//                      Davide Zoni (davide.zoni@polimi.it)
/*********************************************/

package duTypesPkg;

	import wbPkg::*;
//
//1) SIZE AND GLOBAL PARAMETER COMMON TO ALL DEBUG UNITs
//

	// to support 1xdebug unit -> nxdu_local
	localparam DU_NUM_LOCAL_IDS 	 =  2;
	// phy <-> duCtrl localparams (currently implemented phy is an UART)
	localparam PHY_AW				 =	3;
	localparam PHY_DW				 =	8;

	localparam NUM_CPU_BREAKPOINTS	 =	4;
	localparam NUM_CPU_TRIGGERPOINTS =	4;

	// halt signal can be registered or combinational to honor different CPU impls
	localparam DU_LOCAL_REGISTERED_HALT	= 1;
	// used to synchronize duCpu with actual controlled CPU
	// -> IF SET, when HALT/RST->RUN, the 1st CPU advance in the PC is not considered
	localparam DU_LOCAL_ON_RESUME_IS_SHADOW_FIRST_STEPPING_PC 	= 0;
	// -> IF SET,when HALT/RST->RUN, the brkPnt match with the PC of the first CPU advance is not considered
	localparam DU_LOCAL_ON_RESUME_IS_SHADOW_FIRST_BRKPNT_HIT    = 0;

	////////////////////////////////////////////////
	// duGlobal <-> duLocal
	////////////////////////////////////////////////
	localparam DU_LOCALIDW	=	5;
	localparam DU_CMDW 		=	4;
	localparam DU_ADRW		=	12; //address for CSRs, GPRs, FPU regs
	localparam DU_DATW		=	32; //data width of CSRs, GPRs, FPU regs

	////////////////////////////////////////////////
	// Debug memory is used to implement the trace memory
	////////////////////////////////////////////////
	//
	// At the minimum, each entry of the trace memory (DU_TM) is made of a i) timestamp and ii) data
	// i)  The timestamp is differential to the previous stored value, to reduce its size
	// ii) Data can be the address of the executed/committed/fetched instruction or memory access details or ANYTHING ELSE
	//
	// list of traced features for each record in the DU_TraceMemory
	localparam DU_TM_TIMESTAMP_DW			=	10;										// number of bits to store the distance in clock cycles wrt the previous store event
	localparam DU_TM_INST_ADR_DW 			=	32;										// address of the instruction that generated the store event in the DU_TM
	// ... add others, if necessary, to augment the info in each DU_TM entry and
	// fix the DU_BRAM_MEM_DW localparam below, accordingly ...

	localparam DU_BRAM_MEM_NUM_LINES			=	512;									//num lines in a single duBram (Artix7 specific)
	localparam DU_BRAM_MEM_DW				=	DU_TM_TIMESTAMP_DW+DU_TM_INST_ADR_DW;	//data width for a single du bram (Artix7 specific)

	localparam DU_TM_CHUNK_PER_ENTRY			=	(DU_BRAM_MEM_DW-1)/DU_DATW + 1;			// number of DU_DATW parts to get a single DU_TM record
	localparam DU_TM_NUM_BRAM				=	1;										// number of duBram for the trace memory
	localparam DU_TM_NUM_ENTRIES				=	DU_TM_NUM_BRAM * DU_BRAM_MEM_NUM_LINES;	// total number of lines in the DU_TM memory


	//	HOST -> DU - 4 tokens: MMAP_READ, MMAP_WRITE, SPR_READ, SPR_WRITE
	//
	//// read/write on memory mapped registers
	//	mmapReadToken	:= < CMD(16b) + ADDR(32b) >
	//	mmapWriteToken	:= < CMD(16b) + ADDR(32b) + DATA(32b) >
	//
	//// read/write on special purpose registers
	//	sprReadToken	:= < CMD(16b) + ADDR(32b) >
	//	sprWriteToken	:= < CMD(16b) + ADDR(32b) + DATA(32b) >
	//
	// DU -> HOST - 2 tokens: ack/err response to write tokens, data response to read tokens
	//
	// respAckToken	:= < ACK/ERR(8b)>
	// respDataToken:= < ACK/ERR(8b) + DATA(32b) >
	//
	localparam NUM_BYTE_CMD_H2DU		= 2;	// num of bytes of the command packet <command + attributes>
	localparam NUM_BYTE_ADR_H2DU		= 4;	// num of bytes of the address packet
	localparam NUM_BYTE_DAT_H2DU		= 4;	// num of bytes of the data req packet

	localparam NUM_BYTE_DAT_DU2H		= 4;	// num of bytes of the data response
	localparam NUM_BYTE_ACK_ERR_DU2H 	= 1;	// num of bytes of the control response (ack|errCode)

	// MAXIMUM SIZE OF A HOST->DU TOKEN IN BYTE
	localparam NUM_MAX_BYTE_TOKEN_H2DU	= NUM_BYTE_CMD_H2DU + NUM_BYTE_ADR_H2DU + NUM_BYTE_DAT_H2DU;

//
//2) COMMAND field within a TOKEN can be for MMAP or duCpu
//

	// CMD field organization for MMAP ops
	//  |          BYTE 1                 ||      BYTE 0          	   |
	//---------------------------------------------------------------------------
	//	|15 14| 13 |12   10|9 			8 || 7       	  6|5         0|
	//	| BTE | RW | CTI   |selBit[3:2]   || sel_bits[1:0] | tokenType |

	// tokenType
	localparam TOKEN_TYPEW =  6;
	localparam LPOS_BIT_TOKEN_TYPE_CMD_H2DU  = 0;
	localparam HPOS_BIT_TOKEN_TYPE_CMD_H2DU  = LPOS_BIT_TOKEN_TYPE_CMD_H2DU + TOKEN_TYPEW-1;
	// Sel bits
	localparam LPOS_BIT_WB_SEL_CMD_H2DU 		= HPOS_BIT_TOKEN_TYPE_CMD_H2DU + 1;
	localparam HPOS_BIT_WB_SEL_CMD_H2DU 		= LPOS_BIT_WB_SEL_CMD_H2DU	   + 3;
	// CTI
	localparam LPOS_BIT_WB_CTI_CMD_H2DU 	= HPOS_BIT_WB_SEL_CMD_H2DU + 1;
	localparam HPOS_BIT_WB_CTI_CMD_H2DU 	= LPOS_BIT_WB_CTI_CMD_H2DU + 2;
	// RW
	localparam LPOS_BIT_WB_RW_CMD_H2DU 	= HPOS_BIT_WB_CTI_CMD_H2DU + 1;
	localparam HPOS_BIT_WB_RW_CMD_H2DU 	= LPOS_BIT_WB_RW_CMD_H2DU ;
	// BTE
	localparam LPOS_BIT_WB_BTE_CMD_H2DU 	= HPOS_BIT_WB_RW_CMD_H2DU  + 1;
	localparam HPOS_BIT_WB_BTE_CMD_H2DU 	= LPOS_BIT_WB_BTE_CMD_H2DU + 1;

	// HOST->DU token - FIELD POSITION
	localparam LPOS_BIT_DAT_H2DU		= 0;
	localparam HPOS_BIT_DAT_H2DU		= NUM_BYTE_DAT_H2DU * 8 -1;

	localparam LPOS_BIT_ADR_H2DU		= HPOS_BIT_DAT_H2DU + 1;
	localparam HPOS_BIT_ADR_H2DU		= LPOS_BIT_ADR_H2DU + NUM_BYTE_ADR_H2DU*8 -1;

	localparam LPOS_BIT_CMD_H2DU		= HPOS_BIT_ADR_H2DU + 1;
	localparam HPOS_BIT_CMD_H2DU		= LPOS_BIT_CMD_H2DU + NUM_BYTE_CMD_H2DU*8 -1;

	// DU->HOST token - FIELD POSITION
	localparam LPOS_BIT_DAT_DU2H		= 0;
	localparam HPOS_BIT_DAT_DU2H		= NUM_BYTE_DAT_DU2H*8-1;

	localparam LPOS_BIT_ACK_ERR_DU2H	= HPOS_BIT_DAT_DU2H+1;
	localparam HPOS_BIT_ACK_ERR_DU2H	= LPOS_BIT_ACK_ERR_DU2H + NUM_BYTE_ACK_ERR_DU2H*8 -1;

	//
	// CMD field organization for duLocal ops
	//  |      BYTE 1         ||        BYTE 0         |
	//  ------------------------------------------------
	//	|15         11|10     ||7       6|5           0|
	//	|   NOT_USED  |      localId       |  tokenType  |

	localparam LPOS_BIT_CPUID_CMD_H2DU  = HPOS_BIT_TOKEN_TYPE_CMD_H2DU+1;
	localparam HPOS_BIT_CPUID_CMD_H2DU  = LPOS_BIT_CPUID_CMD_H2DU + DU_LOCALIDW;

//
//3) TYPEDEF for token_cmd token_resp and each field
//
	/*	the host controller has a set of internal registers:
	 *  Token_t 	- {cmd,addr,data} 	[phy -> du]
	 *  Response 	- {data,err}		[phy <- du]
	 *	PhyRData_t	- last read data from the phy
	 */
 	// used in interface Fe2Be
	typedef logic [(8*NUM_BYTE_CMD_H2DU)-1:0]  	duCmdH2Du_t;
	typedef logic [(8*NUM_BYTE_ADR_H2DU)-1:0] 	duAddrH2Du_t;
	typedef logic [(8*NUM_BYTE_DAT_H2DU)-1:0] 	duDataH2Du_t;

	typedef logic [(8*NUM_BYTE_ACK_ERR_DU2H)-1:0] 	duAckErrDu2H_t; //1B {6'b000000,ackBit,errBit}
	typedef logic [(8*NUM_BYTE_DAT_DU2H)-1:0] 		duDataDu2H_t;

 	// token of information from the phy as token:={cmd,attr,addr,data} [1B,1B,4B,4B]
	typedef logic [8* (NUM_BYTE_CMD_H2DU + NUM_BYTE_ADR_H2DU+NUM_BYTE_DAT_H2DU)-1:0]	Token_t;
	// counter for the received bytes of the next token
	typedef logic [$clog2(NUM_BYTE_CMD_H2DU + NUM_BYTE_ADR_H2DU+NUM_BYTE_DAT_H2DU)-1:0] CntToken_t;

	// response to the actually processed token. DataResponse + CtrlResponse.
	// The control part of the packet contains the error code (>0) or ack (0).
	// Data response is not mandatory and depends on the processed command
	typedef logic [PHY_DW*(NUM_BYTE_ACK_ERR_DU2H + NUM_BYTE_DAT_DU2H)-1:0]		Response_t;
	// counter for the sent bytes of the response for the current token
	typedef logic [$clog2(NUM_BYTE_ACK_ERR_DU2H + NUM_BYTE_DAT_DU2H):0]		CntResponse_t;

	typedef logic [PHY_DW-1:0] 							PhyData_t;

//
//4) SUPPORTED TOKEN TYPES
//
	// make a token type for the Debug Unit: duGlob and duLoc
	typedef enum logic [HPOS_BIT_TOKEN_TYPE_CMD_H2DU-LPOS_BIT_TOKEN_TYPE_CMD_H2DU:0]
	{
		INV_TOKEN_TYPE										= 'd0,
	//DU_MMAP tokens
		MMAP_READ_TOKEN_TYPE								= 'd1,
		MMAP_WRITE_TOKEN_TYPE								= 'd2,
	//DU_SET/GET_CPU_REGS tokens
		GPR_INT32_READ_TOKEN_TYPE							= 'd3,
		GPR_INT32_WRITE_TOKEN_TYPE							= 'd4,
		GPR_FPU32_READ_TOKEN_TYPE							= 'd5,
		GPR_FPU32_WRITE_TOKEN_TYPE							= 'd6,
	//DU_RST/RESUME/HALT_CPU tokens
		HALT_CPU_TOKEN_TYPE									= 'd7,
		RUN_CPU_TOKEN_TYPE									= 'd8,
		RST_CPU_TOKEN_TYPE									= 'd9,
		GET_duCpu_STATE_TOKEN_TYPE						    = 'd10,
		GET_CPU_PC_TOKEN_TYPE								= 'd11,
	//DU_BRKPNT tokens
		SET_BRKPNT_CPU_TOKEN_TYPE							= 'd12,
		GET_BRKPNT_CPU_TOKEN_TYPE							= 'd13,
		RM_BRKPNT_CPU_TOKEN_TYPE							= 'd14,
		GET_NUM_ACTIVE_BRKPNT_CPU_TOKEN_TYPE				= 'd15,
	//DU_PERF_CNT tokens
		GET_LOW_CYCLECNT_LAST_RUN_PERIOD_TOKEN_TYPE 		= 'd16,
		GET_HIGH_CYCLECNT_LAST_RUN_PERIOD_TOKEN_TYPE 		= 'd17,
		GET_LOW_INSTRCNT_LAST_RUN_PERIOD_TOKEN_TYPE 		= 'd18,
		GET_HIGH_INSTRCNT_LAST_RUN_PERIOD_TOKEN_TYPE 		= 'd19,
	//DU_CPU_STEPPING tokens
		ADVANCE_ONE_STEP_TOKEN_TYPE							= 'd20,
		ECHO_FRONTEND_TOKEN_TYPE							= 'd21,
	//DU_TRGPNT tokens
		SET_TRIGGERPNT_CPU_TOKEN_TYPE						= 'd22,
		GET_TRIGGERPNT_CPU_TOKEN_TYPE						= 'd23,
		RM_TRIGGERPNT_CPU_TOKEN_TYPE						= 'd24,
		GET_NUM_ACTIVE_TRIGGERPNT_CPU_TOKEN_TYPE			= 'd25,
	//DU_DFS
		SET_FREQ_DFS_TOKEN_TYPE								= 'd26,
		GET_FREQ_DFS_TOKEN_TYPE								= 'd27,
		RND_FREQ_DFS_TOKEN_TYPE								= 'd28
	} duTokenType_t;

//
//5) HELPER FUNCTIONS TO MANAGE TOKEN FIELDs
//
	// return if the token is ECHO_FRONTEND (test du communication iface)
	function logic FUNC_isEchoFrontEndToken(input duCmdH2Du_t cmd);
		if( duTokenType_t'(cmd[HPOS_BIT_TOKEN_TYPE_CMD_H2DU:LPOS_BIT_TOKEN_TYPE_CMD_H2DU]) == ECHO_FRONTEND_TOKEN_TYPE )
			return 1;
		else
			return 0;
	endfunction: FUNC_isEchoFrontEndToken

	// return if the token is for MMAP
	function logic FUNC_isMmapToken(input duCmdH2Du_t cmd);
		if(
			duTokenType_t'(cmd[HPOS_BIT_TOKEN_TYPE_CMD_H2DU:LPOS_BIT_TOKEN_TYPE_CMD_H2DU]) == MMAP_READ_TOKEN_TYPE ||
			duTokenType_t'(cmd[HPOS_BIT_TOKEN_TYPE_CMD_H2DU:LPOS_BIT_TOKEN_TYPE_CMD_H2DU]) == MMAP_WRITE_TOKEN_TYPE
			)
			return 1;
		else
			return 0;
	endfunction: FUNC_isMmapToken

	// return if the token is INVALID
	function logic FUNC_isInvalidToken(input duCmdH2Du_t cmd);
		if( duTokenType_t'(cmd[HPOS_BIT_TOKEN_TYPE_CMD_H2DU:LPOS_BIT_TOKEN_TYPE_CMD_H2DU]) == INV_TOKEN_TYPE )
			return 1;
		else
			return 0;
	endfunction: FUNC_isInvalidToken


	//return 1 if the token is intended to be processed by a duLocal, 0 if directed toward Memory (MMAP)
	function logic FUNC_isduLocalToken(input duCmdH2Du_t cmd);

		case(cmd[HPOS_BIT_TOKEN_TYPE_CMD_H2DU:LPOS_BIT_TOKEN_TYPE_CMD_H2DU])
			6'd0:  return 0;	// INVALID_TOKEN_TYPE

			6'd1:  return 0; 	// MMAP_READ_TOKEN_TYPE;
			6'd2:  return 0;	// MMAP_WRITE_TOKEN_TYPE;

			6'd3:  return 1;	// GPR_INT32_READ_TOKEN_TYPE;
			6'd4:  return 1;	// GPR_INT32_WRITE_TOKEN_TYPE;
			6'd5:  return 1;	// GPR_FPU32_READ_TOKEN_TYPE;
			6'd6:  return 1;	// GPR_FPU32_WRITE_TOKEN_TYPE;

			6'd7:  return 1;	// HALT_CPU_TOKEN_TYPE;
			6'd8:  return 1;	// RUN_CPU_TOKEN_TYPE;
			6'd9:  return 1;	// RST_CPU_TOKEN_TYPE;
			6'd10: return 1;	// GET_duCpu_STATE_TOKEN_TYPE
			6'd11: return 1;	// GET_CPU_PC_TOKEN_TYPE

			6'd12: return 1;	// SET_BRKPNT_CPU_TOKEN_TYPE
			6'd13: return 1;	// GET_BRKPNT_CPU_TOKEN_TYPE
			6'd14: return 1;	// RM_BRKPNT_CPU_TOKEN_TYPE
			6'd15: return 1;	// GET_NUM_ACTIVE_BRKPNT_CPU_TOKEN_TYPE1

			6'd16: return 1;	// GET_LOW_CYCLECNT_LAST_RUN_PERIOD_TOKEN_TYPE
			6'd17: return 1;	// GET_HIGH_CYCLECNT_LAST_RUN_PERIOD_TOKEN_TYPE
			6'd18: return 1;	// GET_LOW_INSTRCNT_LAST_RUN_PERIOD_TOKEN_TYPE
			6'd19: return 1;	// GET_HIGH_INSTRCNT_LAST_RUN_PERIOD_TOKEN_TYPE

			6'd20: return 1;	// ADVANCE_ONE_STEP_TOKEN_TYPE
			6'd21: return 0;	// ECHO_FRONTEND_TOKEN_TYPE

			6'd22: return 1;	// SET_TRIGGERPNT_CPU_TOKEN_TYPE
			6'd23: return 1;	// GET_TRIGGERPNT_CPU_TOKEN_TYPE
			6'd24: return 1;	// RM_TRIGGERPNT_CPU_TOKEN_TYPE
			6'd25: return 1;	// GET_NUM_ACTIVE_TRIGGERPNT_CPU_TOKEN_TYPE

			6'd26: return 1; 	// SET_FREQ_DFS_TOKEN_TYPE
			6'd27: return 1; 	// GET_FREQ_DFS_TOKEN_TYPE
			6'd28: return 1;    // RND_FREQ_DFS_TOKEN_TYPE
			
			default: return 1'bx;
		endcase
	endfunction: FUNC_isduLocalToken

	// return if the token is a read (0) or a write (1) (i.e., response is 5 or 1 bytes)
	function logic FUNC_isWriteToken(input duCmdH2Du_t cmd);
		case(cmd[HPOS_BIT_TOKEN_TYPE_CMD_H2DU:LPOS_BIT_TOKEN_TYPE_CMD_H2DU])
			6'd0:  return 0;	// INVALID_TOKEN_TYPE

			6'd1:  return 0; 	// MMAP_READ_TOKEN_TYPE;
			6'd2:  return 1;	// MMAP_WRITE_TOKEN_TYPE;
			
			6'd3:  return 0;	// GPR_INT32_READ_TOKEN_TYPE;
			6'd4:  return 1;	// GPR_INT32_WRITE_TOKEN_TYPE;
			6'd5:  return 0;	// GPR_FPU32_READ_TOKEN_TYPE;
			6'd6:  return 1;	// GPR_FPU32_WRITE_TOKEN_TYPE;
			
			6'd7:  return 0;	// HALT_CPU_TOKEN_TYPE;
			6'd8:  return 0;	// RUN_CPU_TOKEN_TYPE;
			6'd9:  return 0;	// RST_CPU_TOKEN_TYPE;
			6'd10: return 0;	// GET_duCpu_STATE_TOKEN_TYPE
			6'd11: return 0;	// GET_CPU_PC_TOKEN_TYPE

			6'd12: return 1;	// SET_BRKPNT_CPU_TOKEN_TYPE
			6'd13: return 0;	// GET_BRKPNT_CPU_TOKEN_TYPE
			6'd14: return 1;	// RM_BRKPNT_CPU_TOKEN_TYPE
			6'd15: return 0;	// GET_NUM_ACTIVE_BRKPNT_CPU_TOKEN_TYPE

			6'd16: return 0;	// GET_LOW_CYCLECNT_LAST_RUN_PERIOD_TOKEN_TYPE
			6'd17: return 0;	// GET_HIGH_CYCLECNT_LAST_RUN_PERIOD_TOKEN_TYPE
			6'd18: return 0;	// GET_LOW_INSTRCNT_LAST_RUN_PERIOD_TOKEN_TYPE
			6'd19: return 0;	// GET_HIGH_INSTRCNT_LAST_RUN_PERIOD_TOKEN_TYPE
			
			6'd20: return 0;	// ADVANCE_ONE_STEP_TOKEN_TYPE
			6'd21: return 1;	// ECHO_FRONTEND_TOKEN_TYPE

			6'd22: return 1;	// SET_TRIGGERPNT_CPU_TOKEN_TYPE
			6'd23: return 0;	// GET_TRIGGERPNT_CPU_TOKEN_TYPE
			6'd24: return 1;	// RM_TRIGGERPNT_CPU_TOKEN_TYPE
			6'd25: return 0;	// GET_NUM_ACTIVE_TRIGGERPNT_CPU_TOKEN_TYPE

			6'd26: return 1; 	// SET_FREQ_DFS_TOKEN_TYPE
			6'd27: return 0; 	// GET_FREQ_DFS_TOKEN_TYPE
			6'd28: return 1;    // RND_FREQ_DFS_TOKEN_TYPE

			default: return 1'bx;
		endcase
	endfunction: FUNC_isWriteToken

	// get TOKEN_TYPE from the cmd field in the token
	function duTokenType_t FUNC_getTokenType(input duCmdH2Du_t cmd);
		case(cmd[HPOS_BIT_TOKEN_TYPE_CMD_H2DU:LPOS_BIT_TOKEN_TYPE_CMD_H2DU])
			6'd0:  return INV_TOKEN_TYPE;
		//MMAP tokens
			6'd1:  return MMAP_READ_TOKEN_TYPE;
			6'd2:  return MMAP_WRITE_TOKEN_TYPE;
		//DU_SET/GET_REG/CPU tokens
			6'd3:  return GPR_INT32_READ_TOKEN_TYPE;
			6'd4:  return GPR_INT32_WRITE_TOKEN_TYPE;
			6'd5:  return GPR_FPU32_READ_TOKEN_TYPE;
			6'd6:  return GPR_FPU32_WRITE_TOKEN_TYPE;
		//DU_RUN/RST_HALT_CPU tokens
			6'd7:  return HALT_CPU_TOKEN_TYPE;
			6'd8:  return RUN_CPU_TOKEN_TYPE;
			6'd9:  return RST_CPU_TOKEN_TYPE;
			6'd10: return GET_duCpu_STATE_TOKEN_TYPE;
			6'd11: return GET_CPU_PC_TOKEN_TYPE;
		//DU_BRKPNT tokens
			6'd12: return SET_BRKPNT_CPU_TOKEN_TYPE;
			6'd13: return GET_BRKPNT_CPU_TOKEN_TYPE;
			6'd14: return RM_BRKPNT_CPU_TOKEN_TYPE;
			6'd15: return GET_NUM_ACTIVE_BRKPNT_CPU_TOKEN_TYPE;
		//DU_PERFCNT tokens
			6'd16: return GET_LOW_CYCLECNT_LAST_RUN_PERIOD_TOKEN_TYPE;
			6'd17: return GET_HIGH_CYCLECNT_LAST_RUN_PERIOD_TOKEN_TYPE;
			6'd18: return GET_LOW_INSTRCNT_LAST_RUN_PERIOD_TOKEN_TYPE;
			6'd19: return GET_HIGH_INSTRCNT_LAST_RUN_PERIOD_TOKEN_TYPE;
		//DU_CPU_STEPPING token
			6'd20: return ADVANCE_ONE_STEP_TOKEN_TYPE;
			6'd21: return ECHO_FRONTEND_TOKEN_TYPE;
		//DU_TRGPNT tokens
			6'd22: return SET_TRIGGERPNT_CPU_TOKEN_TYPE;
			6'd23: return GET_TRIGGERPNT_CPU_TOKEN_TYPE;
			6'd24: return RM_TRIGGERPNT_CPU_TOKEN_TYPE;
			6'd25: return GET_NUM_ACTIVE_TRIGGERPNT_CPU_TOKEN_TYPE;
		//DU_DFS
			6'd26: return SET_FREQ_DFS_TOKEN_TYPE;
			6'd27: return GET_FREQ_DFS_TOKEN_TYPE;
			6'd28: return RND_FREQ_DFS_TOKEN_TYPE;
		
			default:
				return INV_TOKEN_TYPE;
	endcase
	endfunction: FUNC_getTokenType


	// GET SEL from the cmd field in the token
	function logic[WB_SELW-1:0] FUNC_getWbSelFromToken(input duCmdH2Du_t cmd);
		return cmd[HPOS_BIT_WB_SEL_CMD_H2DU:LPOS_BIT_WB_SEL_CMD_H2DU];
	endfunction: FUNC_getWbSelFromToken

	// GET CTI from the cmd field in the token
	function logic[WB_CTIW-1:0] FUNC_getWbCtiFromToken(input duCmdH2Du_t cmd);
		return cmd[HPOS_BIT_WB_CTI_CMD_H2DU:LPOS_BIT_WB_CTI_CMD_H2DU];
	endfunction: FUNC_getWbCtiFromToken

	// GET BTE from the cmd field in the token
	function logic[WB_BTEW-1:0] FUNC_getWbBteFromToken(input duCmdH2Du_t cmd);
		return cmd[HPOS_BIT_WB_BTE_CMD_H2DU:LPOS_BIT_WB_BTE_CMD_H2DU];
	endfunction: FUNC_getWbBteFromToken

	// GET WE from the cmd field in the token
	function logic[WB_WEW-1:0] FUNC_getWbWeFromToken(input duCmdH2Du_t cmd);
		return cmd[HPOS_BIT_WB_RW_CMD_H2DU:LPOS_BIT_WB_RW_CMD_H2DU];
	endfunction: FUNC_getWbWeFromToken

	// GET CPUID from the cmd field in the token
	function logic[DU_LOCALIDW-1:0] FUNC_getCpuIdFromToken(input duCmdH2Du_t cmd);
		return cmd[HPOS_BIT_CPUID_CMD_H2DU:LPOS_BIT_CPUID_CMD_H2DU];
	endfunction: FUNC_getCpuIdFromToken

//
//6) FSM states for duFrontEnd, duBackEnd, duCpu
//
	///////////////////////////////////////////////////////////////////////
	// FSM for the Debug Front End  (systemverilog type duFrontEndSS_t)  //
	///////////////////////////////////////////////////////////////////////
	typedef enum logic [4:0]
	{
		START_CONFIGURE_PHY 		= 5'd0,
		WE_UART_DIV_REG				= 5'd1,
		SET_UART_DIV_REG			= 5'd2,
		END_CONFIGURE_DEBUG_IFACE	= 5'd3,

		// wait for token cmd contains{cmd,attr}
		WAIT_PHY_FOR_TOKEN_CMD		= 5'd4,
		READ_PHY_FOR_TOKEN_CMD		= 5'd5,

		// rest of the READ or WRITE packet: {addr}
		WAIT_PHY_FOR_TOKEN_ADDR		= 5'd6,
		READ_PHY_FOR_TOKEN_ADDR		= 5'd7,

		// rest of the WRITE token: {data}
		WAIT_PHY_FOR_TOKEN_DATA		= 5'd8,
		READ_PHY_FOR_TOKEN_DATA		= 5'd9,

		// take action for read token <cmd,addr,{data}*>
		START_ELABORATE				= 5'd10,
		WAIT_ELABORATE_DONE			= 5'd11,

		// send resp for token <cmd,addr,datac_chunk>
		WAIT_PHY_TO_SEND_RESP		= 5'd12,
		WRITE_PHY_RESP				= 5'd13,

		// send echo token
		WAIT_PHY_TO_SEND_ECHO		= 5'd14,
		WRITE_PHY_ECHO				= 5'd15,

		FE_ERROR					= 5'd16
	} duFrontEndSS_t;
//
// duBackEnd ss
//
	typedef enum logic [3:0]
	{
		INIT					= 'd0,
		WAIT_FOR_CMD			= 'd1,
		WAIT_DU_LOCAL_RESP		= 'd2,

		IDEX_TOKEN_IF_MMAP_0	= 'd3,
		IDEX_TOKEN_IF_MMAP_1	= 'd4,

		IDEX_TOKEN_IF_duLocal_0	= 'd5,
		IDEX_TOKEN_IF_duLocal_1	= 'd6,

		FINALIZE_CMD			= 'd7
	}duBackEndSS_t;

//
// duCpu ss
//
	typedef enum logic [5:0]
	{
		CPU_TO_RST0							= 'd0,
		CPU_IS_RST							= 'd1,	// stable state (reset state)
		CPU_CMDERR_IN_RST					= 'd2,
		CPU_GETSTATE_RST					= 'd3,

		CPU_TO_RUN0							= 'd4,
		CPU_TO_RUN1							= 'd5,
		CPU_TO_RUN2							= 'd6,
		CPU_IS_RUN							= 'd7,	// stable state (running normal)
		CPU_CMDERR_IN_RUN					= 'd8,
		CPU_GETSTATE_RUN					= 'd9,

		CPU_WAIT_ACK_TO_HALT				= 'd10,
		CPU_IS_HALT							= 'd11,	// stable state (debug mode)
		CPU_CMDERR_IN_HALT					= 'd12,
		CPU_GETSTATE_HALT					= 'd13,

		CPU_WAIT_END_RW						= 'd14,

		CPU_GETNUM_GET_SET_RM_BRKPNT		= 'd15,
		CPU_GETNUM_GET_SET_RM_TRIGGERPNT	= 'd16,

		CPU_GET_CYCLECNT_LAST_RUN_PERIOD	= 'd17,
		CPU_GET_INSTRCNT_LAST_RUN_PERIOD	= 'd18,

		CPU_IS_ONE_STEPPING					= 'd19,	// when CPU is halted we can step with 1 instr granularity
		CPU_GET_CURRENT_PC					= 'd20,

		CPU_TRACEMEM_RST_GET_DATA			= 'd21,

		CPU_GET_NUM_GET_SET_RM_PTABLE		= 'd22,

		CPU_GETNUM_GET_SET_RM_CYCLECOUNT	= 'd23,

		CPU_IS_ERROR						= 'd31

	} duCpuSS_t;


	function integer CLOG2(input integer value);
	begin
		if(value==0)
			CLOG2=0;
		else
		begin
			while(value>0)
			begin
				CLOG2=CLOG2+1;
				value=value>>1;
			end
		end
	end
	endfunction

endpackage: duTypesPkg
