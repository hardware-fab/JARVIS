/*********************************************/
// Author       :   Andrea Galimberti (andrea.galimberti@polimi.it),
//                  Davide Galli (davide.galli@polimi.it),
//                  Davide Zoni (davide.zoni@polimi.it)
//
// Description  :
//
/*********************************************/

`include "defines.vh"

module tb_jarvisSCA();

    parameter VMEM_FILE= "./software_flow/bench/out_vmem/aes.vmem";
    parameter OUT_DATA_RESULT_FILENAME="./software_flow/sim_out_dataResults.txt";
    parameter BENCH_NAME="AES";

	// Below parameters are used to set trigger window (to control the VCD collection)
	// Such values are taken from the objdump analysis of the aes.elf 
	parameter ENABLE_SET_BRK_PNT = 1;	// 1 to allow breakpoints (not necessary for security-wise simulations)
	
    parameter PC_BRK_START = 'h57c;     // Start performance analysis from here
    parameter PC_BRK_STOP  = 'h5c4;     // End performance analysis
   
	parameter ENABLE_SET_TRG_PNT = 1;   // 1 to enable trigger point related VCD dump

	parameter PC_TRG_START = 'h59c;		
	parameter PC_TRG_STOP  = 'h5a8;

/////////////////////////////////////////
// to time CPU execution tim
	parameter 	WORKING_FREQ = 50;


// dataResults vectors 
/////////////////////////////////////////
	parameter VAR1_SIZE 	= 32'd4;
	parameter VAR1_BASE_ADR = 32'h6cc;

	parameter VAR2_SIZE 	= 'd4;
	parameter VAR2_BASE_ADR = 'h6dc;

	parameter VAR3_SIZE 	= 'd0;
	parameter VAR3_BASE_ADR = 'h1bc;

	parameter VAR4_SIZE 	= 'd0;
	parameter VAR4_BASE_ADR = 'h1bc;
/////////////////////////////////////////

	import wbPkg::*;
	import duTypesPkg::*;
	import uartPkg::*;

	// clk freq is linked to uart settings
	parameter HALF_CLK_PERIOD 				= uartPkg::SIM_HALF_CLK_PERIOD_DEF; //10.412@48MHz or 10@50MHz
	parameter CLK_PERIOD 					= HALF_CLK_PERIOD * 2;
	
	// Only to simulate OSC clock on board no UART connection
	parameter HALF_CLK_PERIOD_OSC			= 5; 
	parameter CLK_PERIOD_OSC				= HALF_CLK_PERIOD_OSC * 2;
	
	parameter UART_NUM_CLK_TICKS_BIT 		= uartPkg::SIM_UART_NUM_CLK_TICKS_BIT; // CLK_MHz / (baud_rate)
	parameter UART_NUM_DWORD_BITS			= 8;
	parameter UART_NUM_STOP_BITS			= 1;

	real        start_time,end_time;
    logic clkOSC;
	logic clk;
	logic rst, nrst;
	logic tbSysUartTx;
	logic tbSysUartRx;
	logic tbUsrUartTx;
	logic tbUsrUartRx;
	logic [UART_NUM_DWORD_BITS-1:0] recv_data;
	logic tbTriggerPin0;


	logic [DBG_FLASH_MEM_DW-1:0] 	tb_host2dbg_dat;
	logic 							tb_host2dbg_cyc;
	logic 							tb_dbg2host_ack;

    logic [31:0] memTb [0:WB_MEM_NUM_LINE-1];
    int memIter=0;

	logic ssVcdDump;

    assign nrst =~rst;
    
    ////////////////////////////////////////////////
	// MODULE AND INTERFACE INSTANCES			////
	////////////////////////////////////////////////
	jarvisTop jarvis_top0(
			.CLK_PIN		(clkOSC),
			.NRST_PIN		(nrst),
			//sys uart link
			.sysUartTx		(tbSysUartRx),
			.sysUartRx		(tbSysUartTx),
		`ifndef IMPL_SOC	
			.DATA_HOST2DBG	(tb_host2dbg_dat),
            .CYC_HOST2DBG	(tb_host2dbg_cyc),
            .ACK_DBG2HOST	(tb_dbg2host_ack),
		`endif
		.TRIGGER_PIN_0	(tbTriggerPin0)
	);

	////////////////////////////////////////////////
	// CLOCK GEN: 								////
	// -clkOSC: 100MHz clock on the Nexys4-DDR	////
	// -clk: of the design (clkOSC->|DCM|->clk)	////
	////////////////////////////////////////////////
	always #HALF_CLK_PERIOD clk =~ clk;
	always #HALF_CLK_PERIOD_OSC clkOSC = ~clkOSC;
	
	////////////////////////////////////////////////
	// ACTUAL BENCH			 					////
	////////////////////////////////////////////////

	////////////////////////////////////////////////
	// Control the VCD dump-on/off				//// 
	////////////////////////////////////////////////
	always_ff@(posedge clk)
	begin
		if(rst)
		begin
			$dumpoff;
			ssVcdDump	=	0;
		end
		else
		begin
			if(ssVcdDump==0 && tbTriggerPin0)
			begin
				ssVcdDump=1;
				//$dumpon;
				$display("%t - Start dumping VCD",$time);
			end		
			if(ssVcdDump==1 && ~tbTriggerPin0)
			begin
				ssVcdDump=0;
				//$dumpoff;
				$display("%t - Stop dumping VCD",$time);
			end
		end	
	end

	////////////////////////////////////////////////
	// signals to/from DUT						//// 
	////////////////////////////////////////////////

	integer fid_dataResult;
	integer fid_vmem;
	logic [WB_AW-1:0] tb_addr;
	logic [WB_DW-1:0] tb_data;

	integer 	iterMemRead		= 0;
	integer 	iterMemWrite	= 0;
	integer 	iterRespByte	= 0;
	Response_t 	respArray;
	Token_t 	echoRespArray;
	
	integer     instrCnt = 0;
	
	
	initial
	begin
//
// 1) init all signals and manage reset
//
	clkOSC <= 0;
	clk  <= 0; rst = 1; tbSysUartTx = 1; recv_data = 0;

	// init fast load bin to mem iface
	tb_host2dbg_cyc =0; tb_host2dbg_dat = '0;
	repeat(100) @(posedge clk); rst	<=	0;
	repeat(100) @(posedge clk);


	$display("@%0t: sending du local transaction",
			$time	);

	TASK_setFreq(50);
	
	$display("@%0t: %m DUT response ackErr: 0x%h data: 0x%h",
			$time,
			respArray[HPOS_BIT_ACK_ERR_DU2H:LPOS_BIT_ACK_ERR_DU2H],
			respArray[HPOS_BIT_DAT_DU2H:LPOS_BIT_DAT_DU2H]	);


	repeat(10) @(posedge clk);

	fid_vmem=$fopen(VMEM_FILE,"r");
	assert(fid_vmem) else $fatal();
//		
// 2) write program to mem (from 0x100)
//
	$readmemh(VMEM_FILE,memTb);
	checkBusMemParams();
	$display("###################################");
	$display("## 	Loading vmem file ... (%s) ",VMEM_FILE);
	$display("###################################");



	while(!$feof(fid_vmem))
    begin
        iterMemWrite=iterMemWrite+1;    
  
        $fscanf(fid_vmem,"@%8h %8h\n", tb_addr,tb_data);
        @(posedge clk);
		
        @(posedge clk);
  	
		TASK_wbFastLoadBinTransaction(
			.tb_numIter(iterMemWrite),
			.host2dbg_adr(tb_addr<<2),
			.host2dbg_dat(tb_data)
		);
    end

//    
// 3) halt_CPU (to send token to duLocal directly)
//

	TASK_duLocalTransaction( 
		.duLoc_m2s_tokenType(HALT_CPU_TOKEN_TYPE),
		.duLoc_m2s_cpuid('0),
		
		.duLoc_m2s_adr('0), 
		.duLoc_m2s_dat('0), 
		.duLoc_respArray(respArray)
	);

    
//
// 4) Set breakpoints PC_START / PC_STOP to constrain the free-run simulation
//
	if(ENABLE_SET_BRK_PNT==1)
	begin
		$display("###################################");
		$display("## Configuring Breakpoints ...   ");
		$display("## 	PC_BRKPNT_START: 0x%0h     ", PC_BRK_START);
		$display("## 	PC_BRKPNT_STOP:  0x%0h     ", PC_BRK_STOP);
		$display("###################################");
    	
		TASK_duLocalTransaction( 
    	    .duLoc_m2s_tokenType(SET_BRKPNT_CPU_TOKEN_TYPE),
    	    .duLoc_m2s_cpuid('0),
    	    .duLoc_m2s_adr(PC_BRK_START),
    	    .duLoc_m2s_dat(PC_BRK_START), 
    	    .duLoc_respArray(respArray)
    	);

    	TASK_duLocalTransaction( 
    	    .duLoc_m2s_tokenType(SET_BRKPNT_CPU_TOKEN_TYPE),
    	    .duLoc_m2s_cpuid('0),
    	    .duLoc_m2s_adr(PC_BRK_STOP),
    	    .duLoc_m2s_dat(PC_BRK_STOP), 
    	    .duLoc_respArray(respArray)
    	);
	end
//
// 5) Set trigger points
//
	if(ENABLE_SET_TRG_PNT==1)
	begin
		$display("###################################");
		$display("## Configuring Triggerpoints ... ");
		$display("## 	PC_TRGPNT_START: 0x%0h     ", PC_TRG_START);
		$display("## 	PC_TRGPNT_STOP:  0x%0h     ", PC_TRG_STOP);
		$display("###################################");

    	TASK_duLocalTransaction( 
    	    .duLoc_m2s_tokenType(SET_TRIGGERPNT_CPU_TOKEN_TYPE),
    	    .duLoc_m2s_cpuid('0), 
    	    .duLoc_m2s_adr(PC_TRG_START),
    	    .duLoc_m2s_dat(PC_TRG_START), 
    	    .duLoc_respArray(respArray)
    	);
    	TASK_duLocalTransaction( 
    	    .duLoc_m2s_tokenType(SET_TRIGGERPNT_CPU_TOKEN_TYPE),
    	    .duLoc_m2s_cpuid('0),
    	    .duLoc_m2s_adr(PC_TRG_STOP),
    	    .duLoc_m2s_dat(PC_TRG_STOP), 
    	    .duLoc_respArray(respArray)
    	);

   	end 

	//set working frequency
	TASK_setFreq(WORKING_FREQ);

	start_time = $realtime;

//
// 6) start_CPU (execute crt0.S instructions)
//

	$display("###################################");
	$display("## Starting CPU ...			     ");
	$display("###################################");
	TASK_duLocalTransaction( 
		.duLoc_m2s_tokenType(RUN_CPU_TOKEN_TYPE),
		.duLoc_m2s_cpuid('0),
		.duLoc_m2s_adr('0), 
		.duLoc_m2s_dat('0), 
		.duLoc_respArray(respArray)
	);

//
// 7) wait until the start break point is hit for the first time
//
	if(ENABLE_SET_BRK_PNT==1)
	begin
		// getPC_CPU (send token to duLocal directly)
		TASK_duLocalTransaction( 
				.duLoc_m2s_tokenType(GET_CPU_PC_TOKEN_TYPE),
				.duLoc_m2s_cpuid('0),
				.duLoc_m2s_adr('0), 
				.duLoc_m2s_dat('0), 
				.duLoc_respArray(respArray)
			);
		while(respArray[HPOS_BIT_ACK_ERR_DU2H:LPOS_BIT_ACK_ERR_DU2H]=='b11)
		begin
			repeat(100) @(posedge clk);

			// getPC_CPU (send token to duLocal directly)
			TASK_duLocalTransaction( 
				.duLoc_m2s_tokenType(GET_CPU_PC_TOKEN_TYPE),
				.duLoc_m2s_cpuid('0),
				.duLoc_m2s_adr('0), 
				.duLoc_m2s_dat('0), 
				.duLoc_respArray(respArray)
			);
		end
		$display("##################################");
		$display("## CPU is HALT at PC_BRK: 0x%0h ", PC_BRK_START);
		$display("## Resuming CPU executing	 ...  ");
		$display("##################################");
	end
//
// 8) kick off the CPU again to compute in the critical region 
//
  	TASK_duLocalTransaction( 
        .duLoc_m2s_tokenType(RUN_CPU_TOKEN_TYPE),
        .duLoc_m2s_cpuid('0),
        .duLoc_m2s_adr('0), 
        .duLoc_m2s_dat('0), 
        .duLoc_respArray(respArray)
    );    
//
// 9) wait until the end break point is hit
//
    // getPC_CPU (send token to duLocal directly)
   	TASK_duLocalTransaction( 
		.duLoc_m2s_tokenType(GET_CPU_PC_TOKEN_TYPE),
		.duLoc_m2s_cpuid('0),
		.duLoc_m2s_adr('0), 
		.duLoc_m2s_dat('0), 
		.duLoc_respArray(respArray)
	);
	
	while(respArray[HPOS_BIT_ACK_ERR_DU2H:LPOS_BIT_ACK_ERR_DU2H]=='b11)
	begin
		repeat(100) @(posedge clk);

		// getPC_CPU (send token to duLocal directly)
		TASK_duLocalTransaction( 
			.duLoc_m2s_tokenType(GET_CPU_PC_TOKEN_TYPE),
			.duLoc_m2s_cpuid('0),
			.duLoc_m2s_adr('0), 
			.duLoc_m2s_dat('0), 
			.duLoc_respArray(respArray)
		);
	end
	$display("@%0t: %m TB.DUT response ackErr: 0x%h data: 0x%h",
		$time,
		respArray[HPOS_BIT_ACK_ERR_DU2H:LPOS_BIT_ACK_ERR_DU2H], 
		respArray[HPOS_BIT_DAT_DU2H:LPOS_BIT_DAT_DU2H]	);

	$display("########################################");
	$display("## @%0t: CPU is HALT at PC_BRK: 0x%0h ",$time, PC_BRK_STOP);
	$display("## Wrapping up simulation	 ...   		");
	$display("########################################");
	
	end_time = $realtime;
	
//
// 10) MMAP_READ up to 4 vectors of results and store values into a file for offline accuracy comparison   
//

	$display("########################################");
	$display("## @%0t: Start getting DataResults",$time);
	$display("########################################");
   	
	// opening output data result file
	fid_dataResult=$fopen(OUT_DATA_RESULT_FILENAME,"a");
	assert(fid_dataResult) else $fatal();
	$fwrite(fid_dataResult,"%s ",BENCH_NAME);
	$fflush(fid_dataResult);
	
	//vector of var 1
	$display("## @%0t: Var(BaseAdr=0x%h, Size=%d)",$time, VAR1_BASE_ADR, VAR1_SIZE);
	TASK_getMemVarData(
		.fid_dataResult_tmp	(fid_dataResult),
		.numElem_tmp		(VAR1_SIZE),
		.baseAdr_tmp		(VAR1_BASE_ADR)
	);

	//vector of var 2
	$display("## @%0t: Var2(BaseAdr=0x%h, Size=%d)",$time, VAR2_BASE_ADR, VAR2_SIZE);
	TASK_getMemVarData(
		.fid_dataResult_tmp	(fid_dataResult),
		.numElem_tmp		(VAR2_SIZE),
		.baseAdr_tmp		(VAR2_BASE_ADR)
	);

	//vector of var 3
	$display("## @%0t: Var3(BaseAdr=0x%h, Size=%d)",$time, VAR3_BASE_ADR, VAR3_SIZE);
	TASK_getMemVarData(
		.fid_dataResult_tmp	(fid_dataResult),
		.numElem_tmp		(VAR3_SIZE),
		.baseAdr_tmp		(VAR3_BASE_ADR)
	);

	//vector of var 4
	$display("## @%0t: Var4(BaseAdr=0x%h, Size=%d)",$time, VAR4_BASE_ADR, VAR4_SIZE);
	TASK_getMemVarData(
		.fid_dataResult_tmp	(fid_dataResult),
		.numElem_tmp		(VAR4_SIZE),
		.baseAdr_tmp		(VAR4_BASE_ADR)
	);
	$display("########################################");
	$display("## @%0t: Done getting DataResults",$time);
	$display("########################################");

	$fwrite(fid_dataResult, "time taken  %d ns \n", (end_time-start_time));
	$fflush(fid_dataResult);
	// closing output data result file
	$fclose(fid_dataResult);
//
//	11) finish the simulation
//
	repeat(10) @(posedge clk);
	$fclose(fid_vmem);
	$finish;

end

	task automatic TASK_setFreq;
	input real		f;
	
		TASK_duLocalTransaction(
			.duLoc_m2s_tokenType(SET_FREQ_DFS_TOKEN_TYPE),
			.duLoc_m2s_cpuid(5'd1),
			.duLoc_m2s_adr('0),
			.duLoc_m2s_dat(int'(f*8)), //f<<3
			.duLoc_respArray(respArray)
		);
	
	endtask
	////////////////////////////////////////////////////////////////////////////////
	// TASK TO READOUT RESULTS FROM A VECTOR VARIABLE and STORE THEM IN FILE 	////
	////////////////////////////////////////////////////////////////////////////////
	task automatic TASK_getMemVarData;
		input integer 		fid_dataResult_tmp;
		input integer 		numElem_tmp;
		input logic[31:0]	baseAdr_tmp;

		Response_t 	respArray_tmp;
		integer		iter_tmp;

		for(iter_tmp=0; iter_tmp < numElem_tmp; iter_tmp++)
		begin
		    TASK_wbMmapTransaction(
				.mmap_m2s_tokenType(MMAP_READ_TOKEN_TYPE),
				.mmap_m2s_adr		(baseAdr_tmp + iter_tmp*4),
				.mmap_m2s_dat		(32'b0),
				.mmap_m2s_sel		(4'b1111),
				.mmap_m2s_we		(1'b0),
				.mmap_m2s_cti		(3'b000),
				.mmap_m2s_bte		(2'b00),
				.mmap_respArray	(respArray_tmp)
			);  	
			// get dataValue and write it back to file
			$fwrite(fid_dataResult_tmp,"0x%h ", respArray_tmp[HPOS_BIT_DAT_DU2H:LPOS_BIT_DAT_DU2H]);			
	 		$fflush(fid_dataResult_tmp);
	
		end

	endtask

	////////////////////////////////////////////////////////////////////////
	// TASK TO DU ECHO TRANSACTION SEND TOKEN AND GET IT BACK VERBATIM 	////
	////////////////////////////////////////////////////////////////////////
	task automatic TASK_duEchoTransaction;
		input duTokenType_t 	duLoc_m2s_tokenType;
		input [DU_LOCALIDW-1:0]	duLoc_m2s_cpuid;
		input [DU_ADRW-1:0]		duLoc_m2s_adr;
		input [DU_DATW-1:0]		duLoc_m2s_dat;

		output Token_t   duLoc_respArray;		
		integer duLoc_iterSend	= 0;
		integer duLoc_iterResp	= 0;
		
		@(posedge clk);
		fork
			//SEND TOKENS
			begin
				sendTokenUart(
					{duLoc_m2s_cpuid, duLoc_m2s_tokenType },
					{duLoc_m2s_adr }, 	//32bit adr
					{duLoc_m2s_dat }	//32bit dat
				);
			end
			// WAIT ACK OVER UART
			begin
				for(duLoc_iterResp=0; duLoc_iterResp<10/*NUM_MAX_BYTE_TOKEN_H2DU*/; duLoc_iterResp=duLoc_iterResp+1)
				begin	// WAIT ACK+DATA OVER UART
					recvByteUart(recv_data);
					$display("%t - %d %d %h",$time,duLoc_iterResp,(NUM_MAX_BYTE_TOKEN_H2DU-duLoc_iterResp)*8-1,recv_data);
					duLoc_respArray[(NUM_MAX_BYTE_TOKEN_H2DU-duLoc_iterResp)*8-1 -:8 ] = recv_data;
				end
				$display("@%0t: %m DUT response echo cmd: 0x%h, adr: 0x%h, data: 0x%h",
						$time,
						duLoc_respArray[79:64],
						duLoc_respArray[63:32],
						duLoc_respArray[31:0]
				);
			end
		join
	endtask


	////////////////////////////////////////////////////////////////
	// TASK TO DULOCAL TRANSACTION SEND TOKEN RECEIVE RESPONSE 	////
	// THE UART USING THE PADS									////
	////////////////////////////////////////////////////////////////
	task automatic TASK_duLocalTransaction;
		input duTokenType_t 	duLoc_m2s_tokenType;
		input [DU_LOCALIDW-1:0]	duLoc_m2s_cpuid;
		input [DU_ADRW-1:0]		duLoc_m2s_adr;
		input [DU_DATW-1:0]		duLoc_m2s_dat;

		output Response_t   duLoc_respArray;		
		integer duLoc_iterSend	= 0;
		integer duLoc_iterResp	= 0;
		
		@(posedge clk);
		fork
			//SEND TOKENS
			begin
				sendTokenUart(
					{duLoc_m2s_cpuid, duLoc_m2s_tokenType },
					{duLoc_m2s_adr }, //32bit adr
					{duLoc_m2s_dat }  //32bit dat
				);
			end
			
			// WAIT ACK OVER UART
			begin
				recvByteUart(recv_data);
				duLoc_respArray[HPOS_BIT_ACK_ERR_DU2H -:8 ] = recv_data;
				// data resp
				if(FUNC_isWriteToken ({ duLoc_m2s_cpuid, duLoc_m2s_tokenType  }) )
				begin
					duLoc_respArray[NUM_BYTE_DAT_DU2H*8-1:0] =32'b0;
				end
				else
				begin
					for(duLoc_iterResp=0; duLoc_iterResp<NUM_BYTE_DAT_DU2H; duLoc_iterResp=duLoc_iterResp+1)
					begin	// WAIT ACK+DATA OVER UART
						recvByteUart(recv_data);
						duLoc_respArray[HPOS_BIT_DAT_DU2H - (duLoc_iterResp*8) -:8] = recv_data;
					end

				end
				$display("@%0t: %m DUT response ackErr: 0x%h data: 0x%h",
						$time,
						duLoc_respArray[HPOS_BIT_ACK_ERR_DU2H:LPOS_BIT_ACK_ERR_DU2H], 
						duLoc_respArray[HPOS_BIT_DAT_DU2H:LPOS_BIT_DAT_DU2H]	);
			end
		join
	endtask


	////////////////////////////////////////////////////////////
	// TASK TO FAST LOAD BIN TO MEM USING DGB2MEM IFACE		  //	
	// (	the dgb2mem iface is intended for post synth/impl //
	// 		simulation only even if it can be implemented	) //
	////////////////////////////////////////////////////////////
	task automatic TASK_wbFastLoadBinTransaction;
		input integer		tb_numIter;
		input [WB_AW-1:0]  	host2dbg_adr;
		input [WB_DW-1:0]  	host2dbg_dat;
		
		automatic logic [$clog2(DBG_FLASH_MEM_NPARTS_DAT):0] cntDat;
		automatic logic [$clog2(DBG_FLASH_MEM_NPARTS_ADR):0] cntAdr;
		
		@(posedge clk);
		cntDat=0;
		cntAdr=0;
		$write("@%0t:\t%m (numIter=%0d)\tadr=%h, data=%h ... ",$time,tb_numIter,host2dbg_adr,host2dbg_dat);
		tb_host2dbg_cyc <= 1'b1;
		// send dat	
		repeat(wbPkg::DBG_FLASH_MEM_NPARTS_DAT)
		begin
			tb_host2dbg_dat <= host2dbg_dat[cntDat*DBG_FLASH_MEM_DW+:DBG_FLASH_MEM_DW];
			@(posedge clk);
			cntDat	=	cntDat+1;
		end
		// send adr
		repeat(wbPkg::DBG_FLASH_MEM_NPARTS_DAT)
		begin
			tb_host2dbg_dat <= host2dbg_adr[cntAdr*DBG_FLASH_MEM_DW+:DBG_FLASH_MEM_DW];
			@(posedge clk);
			cntAdr	=	cntAdr+1;
		end
		// wait until transaction with mem is complete
		wait(tb_dbg2host_ack);
		$write("@%0t:\t%m DONE\n", $time);
		tb_host2dbg_cyc <= 1'b0;
	endtask

	////////////////////////////////////////////////////////////
	// TASK TO MMAP TRANSACTION SEND TOKEN RECEIVE RESPONSE ////
	// THE UART USING THE PADS								////
	////////////////////////////////////////////////////////////
	task automatic TASK_wbMmapTransaction;
		input duTokenType_t mmap_m2s_tokenType;
		input [WB_AW-1:0]	mmap_m2s_adr;
		input [WB_DW-1:0]	mmap_m2s_dat;
		input [3:0]			mmap_m2s_sel;
		input				mmap_m2s_we;
		input [2:0]			mmap_m2s_cti;
		input [1:0]			mmap_m2s_bte;

		output Response_t   mmap_respArray;

		integer mmap_iterSend	= 0;
		integer mmap_iterResp	= 0;

		@(posedge clk);
		fork
			//SEND TOKENS
			begin
				sendTokenUart(
					{ 2'b00, mmap_m2s_bte, mmap_m2s_we,  mmap_m2s_cti, mmap_m2s_sel, mmap_m2s_tokenType },
					{mmap_m2s_adr }, //32bit adr
					{mmap_m2s_dat }	//32bit dat
				);
			end
			
			// WAIT ACK OVER UART
			begin
				recvByteUart(recv_data);
				mmap_respArray[HPOS_BIT_ACK_ERR_DU2H -:8 ] = recv_data;
				// data resp
				if(FUNC_isWriteToken ({ 2'b00, mmap_m2s_bte, mmap_m2s_we,  mmap_m2s_cti, mmap_m2s_sel, mmap_m2s_tokenType }) )
				begin
					mmap_respArray[NUM_BYTE_DAT_DU2H*8-1:0] =32'b0;
				end
				else
				begin
					for(mmap_iterResp=0; mmap_iterResp<NUM_BYTE_DAT_DU2H; mmap_iterResp=mmap_iterResp+1)
					begin	// WAIT ACK+DATA OVER UART
						recvByteUart(recv_data);
						mmap_respArray[HPOS_BIT_DAT_DU2H - (mmap_iterResp*8) -:8] = recv_data;
					end

				end
				$display("@%0t: %m DUT response ackErr: 0x%h data: 0x%h",
					$time,
					mmap_respArray[HPOS_BIT_ACK_ERR_DU2H:LPOS_BIT_ACK_ERR_DU2H], 
					mmap_respArray[HPOS_BIT_DAT_DU2H:LPOS_BIT_DAT_DU2H]	);
			end
		join
	endtask: TASK_wbMmapTransaction

	////////////////////////////////////////////////
	// TASK TO SEND A duTOKEN TO 				////
	// THE UART USING THE PADS					////
	////////////////////////////////////////////////
	task sendTokenUart;
		input duCmdH2Du_t 	cmd;
		input duAddrH2Du_t 	adr;
		input duDataH2Du_t 	dat;
	
		automatic logic [3:0] iSendTokenUart='d0;
		begin
			iSendTokenUart = 'd0;
			@(posedge clk);
			$display("@%0t:\t%m cmd=%h (%s), \tadr=%h, data=%h",$time,cmd,FUNC_getTokenType(cmd).name,adr,dat);
		//SEND_CMD
			repeat(NUM_BYTE_CMD_H2DU) 
			begin
	`ifdef DEBUG_UART_PRINTF_VERBOSE
				$display("@%0t %m(%h) duCmd[%0d]", $time, cmd[(NUM_BYTE_CMD_H2DU-iSendTokenUart)*8-1 -:8], (NUM_BYTE_CMD_H2DU-iSendTokenUart));
	`endif
				sendByteUart(cmd[(NUM_BYTE_CMD_H2DU-iSendTokenUart)*8-1 -:8]);
				iSendTokenUart = iSendTokenUart+'d1;
				@(posedge clk);
			end
		//SEND ADDR
			iSendTokenUart = 'd0;
			@(posedge clk);
			repeat(NUM_BYTE_ADR_H2DU) 
			begin		
	`ifdef DEBUG_UART_PRINTF_VERBOSE
				$display("@%0t %m(%h) duAddr[%0d]", $time, adr[(NUM_BYTE_ADR_H2DU-iSendTokenUart)*8-1 -:8], (NUM_BYTE_ADR_H2DU-iSendTokenUart));
	`endif
				sendByteUart(adr[(NUM_BYTE_ADR_H2DU-iSendTokenUart)*8-1 -:8]);
				iSendTokenUart = iSendTokenUart+'d1;
				@(posedge clk);
			end
		//SEND DATA
			if( FUNC_isWriteToken(cmd) )
			begin:IF_WRITE_TOKEN
				iSendTokenUart = 'd0;
				@(posedge clk);
				repeat(NUM_BYTE_DAT_H2DU) 
				begin
		`ifdef DEBUG_UART_PRINTF_VERBOSE
					$display("@%0t %m(%h) duData[%0d]",
							$time,
							dat[(NUM_BYTE_DAT_H2DU-iSendTokenUart)*8-1 -:8],
							(NUM_BYTE_DAT_H2DU-iSendTokenUart));
		`endif
					sendByteUart(dat[(NUM_BYTE_DAT_H2DU-iSendTokenUart)*8-1 -: 8]);
					iSendTokenUart = iSendTokenUart+'d1;
					@(posedge clk);
				end
			end:IF_WRITE_TOKEN
		end

	endtask: sendTokenUart
	
	////////////////////////////////////////////////
	// TASK TO SEND BYTE TO 					////
	// THE UART USING THE PADS					////
	////////////////////////////////////////////////
	task automatic sendByteUart;
		input [UART_NUM_DWORD_BITS-1:0] txData; // 8 bit
		automatic integer iSendByteUart;
		begin
			assert(tbSysUartTx==1); //check tx == 1 if not sending
			@(posedge clk);
	
	`ifdef DEBUG_UART_PRINTF_VERBOSE
			$display("@%0t: START %m(%b)",$time,txData);
	`endif
		//start bit is 0 in uart communication protocol
			tbSysUartTx = '0;
			iSendByteUart	 = 'd0;
			repeat(UART_NUM_CLK_TICKS_BIT) @(posedge clk);
		// send the payload, namely 8 bits
			repeat(UART_NUM_DWORD_BITS)
			begin
				tbSysUartTx = txData[iSendByteUart];
				//$display("@%0t: BIT %m(%b)",$time,tbSysUartTx);
				iSendByteUart    = iSendByteUart+'d1;
				repeat(UART_NUM_CLK_TICKS_BIT) @(posedge clk);	
			end
		// send stop bit/s, that is/are 1
			repeat(UART_NUM_STOP_BITS)
			begin
				tbSysUartTx = '1;
				repeat(UART_NUM_CLK_TICKS_BIT) @(posedge clk);
			end
		// line is 1 when idle, thus keep it set to 1
		end
	endtask: sendByteUart
	////////////////////////////////////////////////
	// TASK TO RECEIVE A BYTE FROM 				////
	// THE UART USING THE PADS					////
	////////////////////////////////////////////////
	task automatic recvByteUart;
		output logic [UART_NUM_DWORD_BITS-1:0] rxDataTemp;
		automatic integer iRecvByteUart=0;
	begin
		iRecvByteUart=0;

		//wait for the start bit
		while(tbSysUartRx == 1) begin @(posedge clk); end
			repeat(UART_NUM_CLK_TICKS_BIT-2) 
			begin	
				if(tbSysUartRx!=0)
				begin
					$display("@%0t: ERROR %m() Start Bit",$time);
					$fatal();
				end
				@(posedge clk);
			end
			//move to the middle of the first bit of the payload
			repeat(UART_NUM_CLK_TICKS_BIT/2) @(posedge clk);
			//recv payload, i.e. 8 bits
			repeat(UART_NUM_DWORD_BITS)
			begin
				//rxDataTemp[iRecvByteUart] <= tbSysUartRx;
				rxDataTemp[iRecvByteUart] = tbSysUartRx;
				iRecvByteUart = iRecvByteUart +'d1;
				repeat(UART_NUM_CLK_TICKS_BIT) @(posedge clk);
			end
		//get first stop bit
		if(tbSysUartRx!=1)
		begin
			$display("@%0t: ERROR tb.recvByteUart() Stop Bit",$time);
			$fatal();
		end
		repeat(UART_NUM_STOP_BITS-1)
		begin
			if(tbSysUartRx!=1)
			begin
				$display("@%0t: ERROR tb.recvByteUart() Stop Bit",$time);
				$fatal();
			end
			//wait for the stop bits after the first one
		end
		//$display("@%0t: Received (%b) = tb.recvByteUart()",$time,rxDataTemp);
	end
	endtask: recvByteUart

	
	task automatic checkBusMemParams;
		`ifdef wb_pkg::LOAD_BIN_FAST32
			assert(wb_pkg::IBUS_DW==32) else $fatal;
		`endif

		`ifdef wb_pkg::LOAD_BIN_FAST64
			assert(wb_pkg::IBUS_DW==64) else $fatal;
		`endif
	endtask

	////////////////////////////////////////////////
	// Fe2Be MONITOR and BASIC SCOREBOARD 		////
	//											////
	// description:								////
	// it checks that the fe2be is semantically ////
	// equivalent to the sent data via Phy		////
	////////////////////////////////////////////////
	always_comb
	begin
`ifdef DEBUG_FE2BE_PRINTF		
		integer i;
		if(wbSoC0.duCtrl0.fe2be0.fe2be_cyc == 1)
		begin:fe2be_monitor
	
			//display fe2be_Iface<cmd,adr,dat>
			$write("@%0t: %m FrontEnd<->BackEnd <cmd,adr,dat>:=<%h, %h, %h>\n",
				$time,
				wbSoC0.duCtrl0.fe2be0.fe2be_cmd,
				wbSoC0.duCtrl0.fe2be0.fe2be_adr,
				wbSoC0.duCtrl0.fe2be0.fe2be_dat
			);	
			// check values of current token:=<cmd,adr,dat>
		end:fe2be_monitor
`endif
	end
	
	////////////////////////////////////////////////
	// Be2Dut MONITOR and BASIC SCOREBOARD 		////
	//											////
	// description:								////
	// it checks that the be2dut correctly 		////
	// propagate a request to the Dut			////
	////////////////////////////////////////////////
	always_comb
	begin
`ifdef DEBUG_BE2DUT_PRINTF
		integer i;
		if(wbSoC0.be2dutWb0.m2s_cyc == 1 && wbSoC0.be2dutWb0.m2s_stb == 1) //simple reads/writes only
		begin:be2dutWB_monitor
	
			//display fe2be_Iface<cmd,adr,dat>
			$write("@%0t: %m FrontEnd<->BackEnd <cmd,adr,dat>:=<%h, %h, %h>\n",
				$time,
				wbSoC0.duCtrl0.fe2be0.fe2be_cmd,
				wbSoC0.duCtrl0.fe2be0.fe2be_adr,
				wbSoC0.duCtrl0.fe2be0.fe2be_dat
			);
			// check values of current token:=<cmd,adr,dat>
		end:be2dutWB_monitor
`endif
	end

endmodule:tb_jarvisSCA
