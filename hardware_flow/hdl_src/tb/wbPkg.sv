/*********************************************/
// Authors			: 	Andrea Galimberti (andrea.galimberti@polimi.it),
//                      Davide Galli (davide.galli@polimi.it),
//                      Davide Zoni (davide.zoni@polimi.it)
//
// Description      :
//
/*********************************************/

package wbPkg;
	////////////////////////////////////////////////////////
	// WISHBONE PARAMETER to the 32 MASTER and SLAVES	////
	////////////////////////////////////////////////////////
	
	localparam WB_DW = 32; // data-word width 
	localparam WB_AW = 32; // address-word width. address up to 4GB 2**32 bytes
	// fast binLoad to mem
	localparam DBG_FLASH_MEM_DW=32;
	localparam DBG_FLASH_MEM_NPARTS_DAT=WB_DW/DBG_FLASH_MEM_DW;
	localparam DBG_FLASH_MEM_NPARTS_ADR=WB_AW/DBG_FLASH_MEM_DW;

	// IBUS localparams (generic, not only for wishbone)
	//  using a 64 bit ibus on a 32bit uarch can load up to 2 instr per clock cycle
	`define LOAD_BIN_FAST64 2;


	localparam IBUS_DW	= 64;
	localparam IBUS_AW	= 32;
	localparam IBUS_ISEL= IBUS_DW/8;

	localparam DBUS_DW	= 32;
	localparam DBUS_AW	= 32;
	localparam DBUS_ISEL= DBUS_DW/8;


	localparam RAM_ADR_SHIFT_AMOUNT	= $clog2(IBUS_ISEL);


	// separating NUM_CPUs and NUM_MASTER allows to reduce by 1 the arbiter
	// width when the duGlobal is not in use for MMAP tokens, i.e., in general after binary
	// dump. By removing duGlobal from wbBus access we can still use duGlobal
	// with duCpu tokens to control CPUs execution!!!!
	// NOTE: we need 2 arbiters. Considering a single-core processor, we can
	// avoid arbitration (save 1 clk cycle for CPU dbus access) when the
	// duGlobal is not in use. (see ENABLE_MMAP_DU, DISABLE_MMAP_DU)
	
    localparam WB_NUM_DBG_BIN_LOAD_TO_MEM_MASTER  = 1;   // num master for fast bin load to mem
	localparam WB_NUM_CPU_MASTER = 1;	                // num masters CPUs only
	
	localparam WB_NUM_MASTER 	= 	1 /*duGlobal*/ 
									+ WB_NUM_CPU_MASTER 
									+ WB_NUM_DBG_BIN_LOAD_TO_MEM_MASTER;	// num masters CPUs + duGlobal
	
	localparam WB_NUM_SLAVE	 	= 5;	                // num slaves attached to the wishbone bus

	// id to connect signals within the wbUncore
	localparam WB_SLAVE_ID_0 = 0; //mem
	localparam WB_SLAVE_ID_1 = 1; //uart
	localparam WB_SLAVE_ID_2 = 2; //timer
	localparam WB_SLAVE_ID_3 = 3; //i2c
	localparam WB_SLAVE_ID_4 = 4; //trng
		
	/* 
	*   The MATCH_ADDR and MATCH_MASK are used to select the slave or to report an error. 
	*	The MATCH_ADDR contains the first address of the memory mapped segment of the slave
	*	The MATCH_MASK zeros lower bits of the address leaving high ones. 
	* 	
	* 	Actual configuration has two slaves, 0 and 1. 
	* 	slave[0] 0-(2^20 - 1); (MEM) 
	* 	slave[1] 2^20 - (2^21 - 1);
	*/
	localparam [WB_NUM_SLAVE*WB_AW-1:0] WB_MATCH_ADDR =  {32'h0040_0000, 32'h0030_0000, 32'h0020_0000, 32'h0010_0000, 32'h0000_0000}; 
	localparam [WB_NUM_SLAVE*WB_AW-1:0] WB_MATCH_MASK =  {32'hfff0_0000, 32'hfff0_0000, 32'hfff0_0000, 32'hfff0_0000, 32'hfff0_0000};


	localparam WB_MEM_SIZE_BYTE  		= 256*1024;
	localparam WB_MEM_LINE_SIZE_BYTE 	= 4;		// 32bits MUST be equal to WB_DW for now

	localparam WB_MEM_NUM_LINE 			= IBUS_DW==32 ? WB_MEM_SIZE_BYTE / WB_MEM_LINE_SIZE_BYTE :
										  IBUS_DW==64 ? WB_MEM_SIZE_BYTE / WB_MEM_LINE_SIZE_BYTE / 2 : 0; 	

	localparam WB_NUM_LINES_32BIT_BRAM36	= 1024;	// 4KB for each + 4Kb for CRC (not used)
	localparam WB_NUM_BRAM36				= WB_MEM_NUM_LINE / WB_NUM_LINES_32BIT_BRAM36;

	localparam WB_MEM_START_ADDR			= 'h100;
	localparam WB_MEM_END_ADDR			= WB_MEM_START_ADDR + WB_MEM_NUM_LINE*(WB_DW/8);

	localparam WB_CTIW	= 3;
	localparam WB_BTEW	= 2;
	localparam WB_WEW	= 1;
	localparam WB_SELW	= 4;

	enum logic [WB_CTIW-1:0]
	{
		WB_CTI_CLASSIC      = 3'b000,
		WB_CTI_CONST_BURST  = 3'b001,	/*access the same address multiple times*/
		WB_CTI_INC_BURST    = 3'b010,	/*access consecutive addresses (see bte)*/
		WB_CTI_END_OF_BURST = 3'b111
	} wbCtiType_t;

	enum logic [WB_BTEW-1:0]
	{
		WB_BTE_LINEAR  = 2'd0,
		WB_BTE_WRAP_4  = 2'd1,
		WB_BTE_WRAP_8  = 2'd2,
		WB_BTE_WRAP_16 = 2'd3
	} wbBteType_t;

	function logic wbIsLastCycle;
		input [WB_CTIW-1:0] cti;
		begin
			case (cti)
				WB_CTI_CLASSIC      : wbIsLastCycle = 1'b1;
				WB_CTI_CONST_BURST  : wbIsLastCycle = 1'b0;
				WB_CTI_INC_BURST    : wbIsLastCycle = 1'b0;
				WB_CTI_END_OF_BURST : wbIsLastCycle = 1'b1;
				default :
				begin	
					$display("%0t %m: Wishbone 4 - Illegal cycle type (CTI=b%b)", $time, cti);
					//$fatal();
				end
			endcase
		end
	endfunction

	// GENERIC FUNCTION - not taylored to IBUS or DBUS
	// Return nextAdr for 32bit, byte addressed architecture
	// input:
	// -> adr_i : current address
	// -> cti_i : cycle type
	// -> bte_i : burst type
	//
	// NOTE: the increment in bytes, if CTI is burst, is word aligned and depends on the data bus size. 
	// 8bit  -> +1, 
	// 16bit -> +2,
	// 32bit -> +4
	// 64bit -> +8
	function [WB_AW-1:0] FUNC_wbNextAdr;
		input [WB_AW-1:0]	adr_i;
		input [2:0] 		cti_i;
		input [1:0] 		bte_i;
		
		logic [WB_AW-1:0] 	adr;
		integer 	 		shift;
		begin
		shift = $clog2(WB_DW/8);
		adr = adr_i >> shift;
		if (cti_i == WB_CTI_INC_BURST)
			case (bte_i)
				WB_BTE_LINEAR   : adr = adr + 1;
				WB_BTE_WRAP_4   : adr = {adr[31:2], adr[1:0]+2'd1};
				WB_BTE_WRAP_8   : adr = {adr[31:3], adr[2:0]+3'd1};
				WB_BTE_WRAP_16  : adr = {adr[31:4], adr[3:0]+4'd1};
				default:
					adr=adr+1;
			endcase // case (burst_type_i)
			return (adr << shift);
		end
	endfunction

	// IBUS NEXTADR func (for 32bit, byte addressed architecture)
	// input:
	// -> adr_i : current address
	// -> cti_i : cycle type
	// -> bte_i : burst type
	//
	// NOTE: the increment in bytes, if CTI is burst, is word aligned and depends on the data bus size. 
	// 8bit  -> +1, 
	// 16bit -> +2,
	// 32bit -> +4
	// 64bit -> +8
	function [WB_AW-1:0] FUNC_wbNextAdr_IBUS;
		input [IBUS_AW-1:0]	adr_i;
		input [2:0] 		cti_i;
		input [1:0] 		bte_i;
		
		logic [IBUS_AW-1:0] adr;
		integer 	 		shift;
		begin
		shift = $clog2(IBUS_DW/8); //shift is related to the data size of IBUS
		adr = adr_i >> shift;
		if (cti_i == WB_CTI_INC_BURST)
		begin
			// single ram0
			if(wbPkg::IBUS_DW==32)
				case (bte_i)
					WB_BTE_LINEAR   : adr =  adr + 1;
					WB_BTE_WRAP_4   : adr = {adr[31:2], adr[1:0]+2'd1};
					WB_BTE_WRAP_8   : adr = {adr[31:3], adr[2:0]+3'd1};
					WB_BTE_WRAP_16  : adr = {adr[31:4], adr[3:0]+4'd1};
					default:
						adr=adr+1;
				endcase
			// dual ram, i.e., ram0 and ram1
			else if(wbPkg::IBUS_DW==64)
			case (bte_i)
				WB_BTE_LINEAR   : adr =  adr + 1;
				WB_BTE_WRAP_4   : adr = {adr[31:1], adr[0]+1'd1};
				WB_BTE_WRAP_8   : adr = {adr[31:2], adr[1:0]+2'd1};
				WB_BTE_WRAP_16  : adr = {adr[31:3], adr[2:0]+3'd1};
				default:
					adr=adr+1;
			endcase
		end
			return (adr << shift);
		end
	endfunction
endpackage:wbPkg
